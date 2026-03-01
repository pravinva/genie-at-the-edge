"""
PostgreSQL NOTIFY listener for Ignition Gateway (8.1 / Jython-safe).

Reads DB connection from:
  [default]Lakebase/Host
  [default]Lakebase/Port
  [default]Lakebase/Database
  [default]Lakebase/User
  [default]Lakebase/Password

Pushes events to Perspective via sendMessage and avoids any writes
to optional Mining telemetry tags.
"""

import system
import time
import traceback
from java.lang import Thread, Runnable
from java.sql import DriverManager, Connection as JdbcConnection
from java.util import Properties
from com.inductiveautomation.ignition.gateway import IgnitionGateway


class LakebaseNotifyListener(Runnable):
    def __init__(self):
        self.logger = system.util.getLogger("LakebaseListener")

        # Required connection tags
        self.host = self._read_tag("[default]Lakebase/Host", "localhost")
        self.port = self._read_tag("[default]Lakebase/Port", 5432)
        self.database = self._read_tag("[default]Lakebase/Database", "historian")
        self.user = self._read_tag("[default]Lakebase/User", "ignition_historian")
        self.password = self._read_tag("[default]Lakebase/Password", "")
        self.ignition_db_connection_name = self._read_tag("[default]Lakebase/DbConnectionName", "lakebase_historian")

        self.jdbc_url = "jdbc:postgresql://{0}:{1}/{2}".format(self.host, self.port, self.database)

        self.channels = [
            "recommendations",
            "recommendations_critical",
            "recommendations_high",
            "recommendations_medium",
            "decisions",
            "commands",
            "agent_health"
        ]

        self.connection = None
        self.pg_connection = None
        self.running = False
        self.last_error = None
        self.last_connect_attempt_ms = None

    def _build_connection_urls(self):
        """
        Build a hostname-based JDBC URL with explicit timeout params.
        Keep hostname (not raw IP) for stable TLS/SNI behavior.
        """
        params = "sslmode=require&connectTimeout=5&socketTimeout=15&tcpKeepAlive=true&loginTimeout=5"
        host_url = "jdbc:postgresql://{0}:{1}/{2}?{3}".format(self.host, self.port, self.database, params)
        return [host_url]

    def _list_registered_drivers(self):
        drivers = []
        try:
            enum = DriverManager.getDrivers()
            while enum.hasMoreElements():
                try:
                    drivers.append(str(enum.nextElement().getClass().getName()))
                except Exception:
                    drivers.append("<unknown-driver>")
        except Exception as e:
            drivers.append("<driver-enum-error:{0}>".format(str(e)))
        return drivers

    def _collect_jdbc_diagnostics(self, candidate_url):
        """
        Gather diagnostics before each JDBC attempt to speed up root cause analysis.
        Keep this method lightweight and avoid APIs that can throw
        uncaught driver-resolution errors in some Ignition runtimes.
        """
        diag = {
            "host": str(self.host),
            "resolved_ip": "<skipped>",
            "driver_manager_driver": "<skipped>",
            "driver_manager_driver_error": "<skipped>",
            "registered_drivers": []
        }

        diag["registered_drivers"] = self._list_registered_drivers()
        return diag

    def _open_connection(self, candidate_url, props):
        """
        Open connection using Ignition Gateway datasource manager.
        DriverManager and system.db.getConnection can fail in some
        gateway scripting classloader/signature contexts.
        """
        self.logger.info("Using Ignition datasource connection: {0}".format(self.ignition_db_connection_name))
        try:
            gateway = IgnitionGateway.get()
            if gateway is None:
                raise Exception("IgnitionGateway.get() returned None")

            ds_manager = gateway.getDatasourceManager()
            if ds_manager is None:
                raise Exception("Gateway datasource manager is unavailable")

            conn = ds_manager.getConnection(str(self.ignition_db_connection_name))
            if conn is None:
                raise Exception("DatasourceManager.getConnection returned None")
            return conn
        except Exception as e:
            raise Exception(
                "Ignition datasource connect failed. "
                "datasource={0} error={1}".format(self.ignition_db_connection_name, str(e))
            )

    def _read_tag(self, path, default_value):
        try:
            qv = system.tag.readBlocking([path])[0]
            if qv is None or qv.value is None:
                return default_value
            return qv.value
        except Exception as e:
            self.logger.warn("Could not read tag {0}: {1}".format(path, str(e)))
            return default_value

    def _class_name(self, obj):
        try:
            return str(obj.getClass().getName())
        except Exception:
            return str(type(obj))

    def _try_unwrap_connection(self, conn):
        # 1) Generic JDBC unwrap to java.sql.Connection
        try:
            if hasattr(conn, "isWrapperFor") and conn.isWrapperFor(JdbcConnection):
                inner = conn.unwrap(JdbcConnection)
                if inner is not None and inner is not conn:
                    return inner
        except Exception:
            pass

        # 2) PostgreSQL-specific unwrap using the connection's classloader.
        # This avoids relying on the gateway script classloader seeing PG classes.
        try:
            cl = conn.getClass().getClassLoader()
            if cl is not None and hasattr(conn, "isWrapperFor") and hasattr(conn, "unwrap"):
                for cname in ["org.postgresql.PGConnection", "org.postgresql.jdbc.PgConnection"]:
                    try:
                        pg_cls = cl.loadClass(cname)
                        if conn.isWrapperFor(pg_cls):
                            inner = conn.unwrap(pg_cls)
                            if inner is not None and inner is not conn:
                                return inner
                    except Exception:
                        pass
        except Exception:
            pass
        return None

    def _try_named_unwrap_methods(self, conn):
        method_names = [
            "getUnderlyingConnection",
            "getConnection",
            "getDelegate",
            "getInnermostDelegate",
            "getRawConnection",
            "getDelegateInternal"
        ]

        # Try public methods first.
        for m in method_names:
            try:
                method = conn.getClass().getMethod(m, [])
                cand = method.invoke(conn, [])
                if cand is not None and cand is not conn:
                    return cand
            except Exception:
                pass

        # Then try declared (possibly non-public) methods up class hierarchy.
        cls = conn.getClass()
        while cls is not None:
            for m in method_names:
                try:
                    method = cls.getDeclaredMethod(m, [])
                    method.setAccessible(True)
                    cand = method.invoke(conn, [])
                    if cand is not None and cand is not conn:
                        return cand
                except Exception:
                    pass
            try:
                cls = cls.getSuperclass()
            except Exception:
                cls = None
        return None

    def _try_declared_fields(self, conn):
        field_names = ["delegate", "connection", "wrappedConnection", "underlyingConnection", "inner", "target"]
        cls = conn.getClass()
        while cls is not None:
            for fname in field_names:
                try:
                    f = cls.getDeclaredField(fname)
                    f.setAccessible(True)
                    cand = f.get(conn)
                    if cand is not None and cand is not conn:
                        return cand
                except Exception:
                    pass
            try:
                cls = cls.getSuperclass()
            except Exception:
                cls = None
        return None

    def _resolve_notification_connection(self, base_conn):
        """
        DatasourceManager may return a wrapped connection object.
        Walk common wrapper methods to find the underlying PG connection
        that exposes getNotifications(...).
        """
        current = base_conn
        seen = {}
        for depth in range(0, 8):
            if current is None:
                break

            cname = self._class_name(current)

            # Found a connection object that supports PostgreSQL notification polling.
            try:
                getattr(current, "getNotifications")
                self.logger.info("Resolved notification connection class: {0}".format(cname))
                return current
            except Exception:
                pass

            key = cname + "@" + str(depth)
            if seen.get(key):
                break
            seen[key] = True

            next_conn = self._try_unwrap_connection(current)
            if next_conn is None:
                next_conn = self._try_named_unwrap_methods(current)
            if next_conn is None:
                next_conn = self._try_declared_fields(current)

            if next_conn is None:
                break
            current = next_conn

        return None

    def _poll_notifications(self, timeout_ms):
        """
        Poll notifications using whichever PGConnection getNotifications signature
        is available in this runtime.
        """
        if self.pg_connection is None:
            return None
        try:
            return self.pg_connection.getNotifications(timeout_ms)
        except TypeError:
            return self.pg_connection.getNotifications()

    def connect(self):
        props = Properties()
        try:
            self.last_connect_attempt_ms = system.date.toMillis(system.date.now())
            self.logger.info("Connect step 1/5: validating credentials tag values")
            if not self.password:
                self.logger.error("Lakebase password tag is empty: [default]Lakebase/Password")
                return False

            # Avoid explicit classloading here; it can block in some 8.1 runtimes.
            self.logger.info("Connect step 2/5: skipping explicit JDBC classloading")

            self.logger.info("Connect step 3/5: preparing JDBC properties")
            props.setProperty("user", str(self.user))
            props.setProperty("password", str(self.password))
            props.setProperty("sslmode", "require")

            DriverManager.setLoginTimeout(15)
            urls = self._build_connection_urls()
            self.logger.info("Connect step 4/5: opening connection (candidates={0})".format(len(urls)))

            last_conn_error = None
            self.connection = None
            for i in range(len(urls)):
                candidate = urls[i]
                try:
                    self.logger.info("JDBC attempt {0}/{1}: {2}".format(i + 1, len(urls), candidate))
                    self.connection = self._open_connection(candidate, props)
                    self.logger.info("JDBC attempt {0}/{1}: success".format(i + 1, len(urls)))
                    break
                except Exception as ce:
                    last_conn_error = ce
                    self.logger.warn("JDBC attempt {0}/{1}: failed: {2}".format(i + 1, len(urls), str(ce)))

            if self.connection is None:
                if last_conn_error:
                    raise last_conn_error
                raise Exception("No JDBC candidates available for host {0}".format(self.host))

            self.connection.setAutoCommit(True)
            self.pg_connection = self._resolve_notification_connection(self.connection)
            if self.pg_connection is None:
                raise Exception(
                    "Connected but could not resolve PG notification connection. base_class={0}".format(
                        self._class_name(self.connection)
                    )
                )

            self.logger.info("Connect step 5/5: registering LISTEN channels")
            stmt = self.connection.createStatement()
            for channel in self.channels:
                stmt.execute("LISTEN {0}".format(channel))
                self.logger.info("Listening on channel: {0}".format(channel))
            stmt.close()

            self.last_error = None
            self.logger.info("Lakebase NOTIFY listener connected successfully")
            return True
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(
                "Failed to connect to Lakebase: {0} | host={1} port={2} db={3} user={4} password_set={5}".format(
                    str(e), str(self.host), str(self.port), str(self.database), str(self.user), bool(self.password)
                )
            )
            self.logger.error("Connect traceback:\n{0}".format(traceback.format_exc()))
            return False

    def run(self):
        self.running = True
        self.logger.info("Starting NOTIFY listener thread...")
        self.logger.info("Run loop pre-check: beginning initial connect")

        if not self.connect():
            self.logger.error("Initial connection failed; listener not started.")
            self.running = False
            return

        while self.running:
            try:
                notifications = self._poll_notifications(1000)
                if notifications:
                    for notification in notifications:
                        self.handle_notification(notification)

                self.check_connection_health()
            except Exception as e:
                self.last_error = str(e)
                self.logger.error("Error in listen loop: {0}".format(str(e)))
                if "getNotifications" in str(e):
                    self.logger.error(
                        "Connection object does not expose getNotifications(); "
                        "verify PostgreSQL JDBC driver module is enabled."
                    )
                self.logger.error("Listen loop traceback:\n{0}".format(traceback.format_exc()))
                time.sleep(2)
                self._safe_reconnect()

        self.cleanup()

    def _safe_reconnect(self):
        try:
            self.logger.info("Attempting reconnect...")
            self.cleanup()
        except Exception:
            pass
        if not self.connect():
            self.logger.warn("Reconnect attempt failed; will retry.")

    def _safe_parse_payload(self, payload_str):
        try:
            return system.util.jsonDecode(payload_str)
        except Exception:
            self.logger.warn("Payload is not valid JSON: {0}".format(payload_str))
            return {"raw_payload": payload_str}

    def _normalize_recommendation_payload(self, payload):
        return {
            "data": {
                "recommendationId": payload.get("recommendation_id"),
                "equipmentId": payload.get("equipment_id"),
                "issueType": payload.get("issue_type"),
                "severity": payload.get("severity"),
                "confidenceScore": payload.get("confidence_score"),
                "recommendedAction": payload.get("recommended_action"),
                "timestamp": payload.get("timestamp")
            }
        }

    def _normalize_status_payload(self, payload):
        return {
            "data": {
                "recommendationId": payload.get("recommendation_id"),
                "newStatus": payload.get("new_status"),
                "operatorId": payload.get("operator") or payload.get("operator_id"),
                "operatorNotes": payload.get("operator_notes"),
                "timestamp": payload.get("timestamp")
            }
        }

    def handle_notification(self, notification):
        try:
            channel = notification.getName()
            payload_str = notification.getParameter()
            payload = self._safe_parse_payload(payload_str)

            self.logger.info("[{0}] Event received".format(channel))

            if channel.startswith("recommendations"):
                self.handle_recommendation(payload)
            elif channel == "decisions":
                self.handle_decision(payload)
            elif channel == "commands":
                self.handle_command(payload)
            elif channel == "agent_health":
                self.handle_agent_health(payload)
        except Exception as e:
            self.last_error = str(e)
            self.logger.error("Error handling notification: {0}".format(str(e)))

    def handle_recommendation(self, payload):
        try:
            msg = self._normalize_recommendation_payload(payload)
            system.perspective.sendMessage(
                "ML_RECOMMENDATION_UPDATE",
                payload=msg,
                scope="session"
            )

            if (payload.get("severity") or "").lower() == "critical":
                system.perspective.sendMessage(
                    "criticalAlert",
                    payload=msg,
                    scope="session"
                )

            self.logger.info(
                "Recommendation pushed: {0} / {1}".format(
                    payload.get("recommendation_id"), payload.get("equipment_id")
                )
            )
        except Exception as e:
            self.last_error = str(e)
            self.logger.error("Error handling recommendation: {0}".format(str(e)))

    def handle_decision(self, payload):
        try:
            msg = self._normalize_status_payload(payload)
            system.perspective.sendMessage(
                "ML_RECOMMENDATION_STATUS",
                payload=msg,
                scope="session"
            )
            self.logger.info(
                "Decision pushed: {0} -> {1}".format(
                    payload.get("recommendation_id"), payload.get("new_status")
                )
            )
        except Exception as e:
            self.last_error = str(e)
            self.logger.error("Error handling decision: {0}".format(str(e)))

    def handle_command(self, payload):
        try:
            system.perspective.sendMessage(
                "commandExecution",
                payload=payload,
                scope="session"
            )
        except Exception as e:
            self.last_error = str(e)
            self.logger.error("Error handling command: {0}".format(str(e)))

    def handle_agent_health(self, payload):
        try:
            system.perspective.sendMessage(
                "agentHealth",
                payload=payload,
                scope="session"
            )
        except Exception as e:
            self.last_error = str(e)
            self.logger.error("Error handling agent health: {0}".format(str(e)))

    def check_connection_health(self):
        try:
            if self.connection is None or self.connection.isClosed():
                self.logger.warn("Connection is closed; reconnecting.")
                self._safe_reconnect()
                return

            stmt = self.connection.createStatement()
            rs = stmt.executeQuery("SELECT 1")
            rs.close()
            stmt.close()
        except Exception as e:
            self.last_error = str(e)
            self.logger.warn("Connection health check failed: {0}".format(str(e)))
            self.logger.warn("Health check traceback:\n{0}".format(traceback.format_exc()))
            self._safe_reconnect()

    def stop(self):
        self.running = False
        self.logger.info("Stopping NOTIFY listener...")

    def cleanup(self):
        try:
            if self.connection and (not self.connection.isClosed()):
                stmt = self.connection.createStatement()
                for channel in self.channels:
                    try:
                        stmt.execute("UNLISTEN {0}".format(channel))
                    except Exception:
                        pass
                stmt.close()
                self.connection.close()
            self.connection = None
            self.pg_connection = None
        except Exception as e:
            self.last_error = str(e)
            self.logger.warn("Cleanup warning: {0}".format(str(e)))


def start_lakebase_listener():
    """Call from Gateway Startup script."""
    logger = system.util.getLogger("LakebaseListener")
    try:
        existing = system.util.getGlobals().get("lakebaseListener")
        existing_thread = system.util.getGlobals().get("lakebaseListenerThread")
        if existing:
            is_running = getattr(existing, "running", False)
            thread_alive = False
            try:
                thread_alive = bool(existing_thread and existing_thread.isAlive())
            except Exception:
                thread_alive = False

            conn_ok = False
            try:
                conn_ok = bool(existing.connection and (not existing.connection.isClosed()))
            except Exception:
                conn_ok = False

            if is_running and thread_alive and conn_ok:
                logger.info("Listener already running and healthy.")
                return

            logger.warn(
                "Found stale listener state; forcing restart. "
                "running={0} thread_alive={1} conn_ok={2} last_error={3}".format(
                    is_running, thread_alive, conn_ok, getattr(existing, "last_error", None)
                )
            )
            try:
                existing.stop()
                existing.cleanup()
            except Exception:
                pass

        listener = LakebaseNotifyListener()
        thread = Thread(listener, "LakebaseNotifyListener")
        thread.setDaemon(True)
        thread.start()

        system.util.getGlobals()["lakebaseListener"] = listener
        system.util.getGlobals()["lakebaseListenerThread"] = thread

        logger.info(
            "Lakebase NOTIFY listener start requested. host={0} port={1} db={2} user={3} password_set={4}".format(
                listener.host, listener.port, listener.database, listener.user, bool(listener.password)
            )
        )
    except Exception as e:
        logger.error("Failed to start listener: {0}".format(str(e)))
        logger.error("Startup traceback:\n{0}".format(traceback.format_exc()))


def stop_lakebase_listener():
    """Call from Gateway Shutdown script."""
    logger = system.util.getLogger("LakebaseListener")
    try:
        listener = system.util.getGlobals().get("lakebaseListener")
        if listener:
            listener.stop()

        thread = system.util.getGlobals().get("lakebaseListenerThread")
        if thread:
            try:
                thread.join(5000)
            except Exception:
                pass

        logger.info("Lakebase NOTIFY listener stopped.")
    except Exception as e:
        logger.error("Error stopping listener: {0}".format(str(e)))
        logger.error("Shutdown traceback:\n{0}".format(traceback.format_exc()))


def debug_lakebase_listener_status():
    """
    Logs and returns detailed listener status from Gateway scope.
    Call from a Gateway Event Script or message handler.
    """
    logger = system.util.getLogger("LakebaseListener")
    g = system.util.getGlobals()
    listener = g.get("lakebaseListener")
    thread = g.get("lakebaseListenerThread")

    status = {
        "listener_exists": bool(listener),
        "thread_exists": bool(thread),
        "running": False,
        "thread_alive": False,
        "has_connection": False,
        "connection_closed": None,
        "last_error": None,
        "last_connect_attempt_ms": None
    }

    if listener:
        status["running"] = bool(getattr(listener, "running", False))
        status["last_error"] = getattr(listener, "last_error", None)
        status["last_connect_attempt_ms"] = getattr(listener, "last_connect_attempt_ms", None)
        try:
            status["has_connection"] = bool(listener.connection is not None)
            if listener.connection is not None:
                status["connection_closed"] = bool(listener.connection.isClosed())
        except Exception as e:
            status["last_error"] = "{0} | conn_state_error={1}".format(status["last_error"], str(e))

    if thread:
        try:
            status["thread_alive"] = bool(thread.isAlive())
        except Exception:
            status["thread_alive"] = False

    logger.info("Listener status: {0}".format(status))
    return status