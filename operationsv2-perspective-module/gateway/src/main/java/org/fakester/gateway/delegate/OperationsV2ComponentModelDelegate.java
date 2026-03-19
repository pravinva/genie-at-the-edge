package org.fakester.gateway.delegate;

import com.inductiveautomation.ignition.common.gson.JsonElement;
import com.inductiveautomation.ignition.common.gson.JsonArray;
import com.inductiveautomation.ignition.common.gson.JsonObject;
import com.inductiveautomation.ignition.common.gson.JsonParser;
import com.inductiveautomation.ignition.common.script.ScriptManager;
import com.inductiveautomation.ignition.gateway.datasource.SRConnection;
import com.inductiveautomation.perspective.gateway.api.Component;
import com.inductiveautomation.perspective.gateway.api.ComponentModelDelegate;
import com.inductiveautomation.perspective.gateway.messages.EventFiredMsg;
import org.fakester.gateway.RadGatewayHook;
import org.python.core.Py;
import org.python.core.PyObject;
import org.python.core.PyStringMap;

import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/**
 * Delegate for the Operations V2 component.
 *
 * Handles button interactions from the React component and persists
 * decision actions into the configured Ignition datasource.
 */
public class OperationsV2ComponentModelDelegate extends ComponentModelDelegate {

    public static final String EVENT_DECISION = "opsv2-decision-event";
    public static final String EVENT_DECISION_RESULT = "opsv2-decision-result-event";
    public static final String EVENT_GENIE_ASK = "opsv2-genie-ask-event";
    public static final String EVENT_GENIE_CLEAR = "opsv2-genie-clear-event";
    public static final String EVENT_GENIE_RESULT = "opsv2-genie-result-event";
    public static final String EVENT_REFRESH = "opsv2-refresh-event";
    public static final String EVENT_REFRESH_RESULT = "opsv2-refresh-result-event";
    public static final String EVENT_TREND = "opsv2-trend-event";
    public static final String EVENT_TREND_RESULT = "opsv2-trend-result-event";

    public OperationsV2ComponentModelDelegate(Component component) {
        super(component);
    }

    @Override
    protected void onStartup() {
        // no-op
    }

    @Override
    protected void onShutdown() {
        // no-op
    }

    @Override
    public void handleEvent(EventFiredMsg message) {
        String eventName = message.getEventName();
        JsonObject payload = message.getEvent();

        if (EVENT_DECISION.equals(eventName)) {
            handleDecision(payload);
            return;
        }

        if (EVENT_GENIE_ASK.equals(eventName)) {
            handleGenieAsk(payload);
            return;
        }

        if (EVENT_GENIE_CLEAR.equals(eventName)) {
            JsonObject out = new JsonObject();
            out.addProperty("transcript", "GENIE: Ready.");
            out.addProperty("busy", false);
            fireEvent(EVENT_GENIE_RESULT, out);
            return;
        }

        if (EVENT_REFRESH.equals(eventName)) {
            handleRefresh(payload);
            return;
        }

        if (EVENT_TREND.equals(eventName)) {
            handleTrend(payload);
        }
    }

    private void handleDecision(JsonObject payload) {
        JsonObject out = new JsonObject();

        try {
            String datasource = getString(payload, "databaseConnection", "lakebase_historian");
            String decision = normalizeDecision(getString(payload, "decision", "deferred"));
            String equipmentId = getString(payload, "equipment_id", "");
            String scoredAt = getString(payload, "scored_at", "");
            String operatorId = getString(payload, "operator_id", "operator");
            String feedbackText = getString(payload, "feedback_text", "");

            if (equipmentId.isEmpty()) {
                throw new SQLException("equipment_id is required");
            }

            if (scoredAt.isEmpty()) {
                // fallback to current time on the DB side if the UI omitted scored_at
                scoredAt = null;
            }

            String sql = scoredAt == null
                ? "INSERT INTO public.operator_feedback (equipment_id, scored_at, decision, operator_id, feedback_text) VALUES (?, now(), ?, ?, ?)"
                : "INSERT INTO public.operator_feedback (equipment_id, scored_at, decision, operator_id, feedback_text) VALUES (?, CAST(? AS timestamp), ?, ?, ?)";

            try (SRConnection conn = RadGatewayHook.getGatewayContext().getDatasourceManager().getConnection(datasource);
                 PreparedStatement ps = conn.prepareStatement(sql)) {
                ps.setString(1, equipmentId);
                if (scoredAt == null) {
                    ps.setString(2, decision);
                    ps.setString(3, operatorId);
                    ps.setString(4, feedbackText);
                } else {
                    ps.setString(2, scoredAt);
                    ps.setString(3, decision);
                    ps.setString(4, operatorId);
                    ps.setString(5, feedbackText);
                }
                int count = ps.executeUpdate();
                out.addProperty("ok", count > 0);
                out.addProperty("message", "Recorded " + decision + " for " + equipmentId);
            }
        } catch (Exception e) {
            out.addProperty("ok", false);
            out.addProperty("message", "Decision write failed: " + e.getMessage());
            log.errorf("OperationsV2 decision handler failed: %s", e.getMessage());
        }

        fireEvent(EVENT_DECISION_RESULT, out);
    }

    private void handleGenieAsk(JsonObject payload) {
        String question = getString(payload, "question", "");
        String transcript = getString(payload, "transcript", "GENIE: Ready.");
        String conversationId = getString(payload, "conversationId", "");
        JsonObject out = new JsonObject();

        if (question.trim().isEmpty()) {
            out.addProperty("busy", false);
            out.addProperty("transcript", transcript);
            out.addProperty("conversationId", conversationId);
            out.addProperty("message", "Ask skipped: empty question");
            fireEvent(EVENT_GENIE_RESULT, out);
            return;
        }

        try {
            // Use the session-scoped script manager so project library scripts are resolvable.
            ScriptManager scriptManager = component.getSession().getScriptManager();
            String projectName = component.getSession().getProjectName();
            log.infof("OpsV2 GENIE_ASK received. project=%s conversationId=%s", projectName, conversationId);

            PyObject result = invokeGenieQuery(scriptManager, question, conversationId);

            String responseText = getPyField(result, "response", "No response.");
            String nextConversationId = getPyField(result, "conversationId", conversationId);
            String sqlText = getPyField(result, "sql", "");
            String tableMarkdown = getPyField(result, "tableMarkdown", "");

            String nextTranscript = transcript
                + "\n\nOPERATOR: " + question
                + "\nGENIE: " + responseText;

            out.addProperty("busy", false);
            out.addProperty("transcript", nextTranscript);
            out.addProperty("conversationId", nextConversationId);
            out.addProperty("sql", sqlText);
            out.addProperty("tableMarkdown", tableMarkdown);
            out.addProperty("message", "Genie response received");
            log.infof("OpsV2 Genie invoke succeeded. nextConversationId=%s", nextConversationId);
        } catch (Exception e) {
            out.addProperty("busy", false);
            out.addProperty("transcript", transcript + "\n\nOPERATOR: " + question + "\nGENIE ERROR: " + e.getMessage());
            out.addProperty("conversationId", conversationId);
            out.addProperty("sql", "");
            out.addProperty("tableMarkdown", "");
            out.addProperty("message", "Genie call failed");
            log.errorf("OperationsV2 genie handler failed: %s", e.getMessage());
        }

        fireEvent(EVENT_GENIE_RESULT, out);
    }

    private void handleRefresh(JsonObject payload) {
        String datasource = getString(payload, "databaseConnection", "lakebase_historian");
        JsonObject out = new JsonObject();
        JsonArray rows = new JsonArray();
        JsonObject latestByEquipment = new JsonObject();

        String sql =
            "SELECT "
                + "r.equipment_id, "
                + "r.severity, "
                + "ROUND(COALESCE(r.anomaly_score, 0)::numeric, 3) AS anomaly_score, "
                + "ROUND(COALESCE(r.confidence, 0)::numeric, 2) AS confidence, "
                + "COALESCE(r.recommendation_text, '') AS recommendation_text, "
                + "COALESCE(r.estimated_ttf, 0) AS estimated_ttf, "
                + "TO_CHAR(r.scored_at, 'YYYY-MM-DD HH24:MI:SS.US') AS scored_at, "
                + "TO_CHAR(r.scored_at, 'YYYY-MM-DD HH24:MI:SS') AS scored_at_display "
                + "FROM public.ml_recommendations r "
                + "WHERE NOT EXISTS ( "
                + "  SELECT 1 "
                + "  FROM public.operator_feedback f "
                + "  WHERE f.equipment_id = r.equipment_id "
                + "    AND f.scored_at = r.scored_at "
                + ") "
                + "ORDER BY r.scored_at DESC "
                + "LIMIT 200";

        try (SRConnection conn = RadGatewayHook.getGatewayContext().getDatasourceManager().getConnection(datasource);
             PreparedStatement ps = conn.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {

            while (rs.next()) {
                JsonObject row = new JsonObject();
                String equipmentId = rs.getString("equipment_id");
                String severity = rs.getString("severity");
                String anomalyScore = rs.getString("anomaly_score");
                String confidence = rs.getString("confidence");
                row.addProperty("equipment_id", equipmentId);
                row.addProperty("severity", severity);
                row.addProperty("anomaly_score", anomalyScore);
                row.addProperty("confidence", confidence);
                row.addProperty("recommendation_text", rs.getString("recommendation_text"));
                row.addProperty("estimated_ttf", rs.getString("estimated_ttf"));
                row.addProperty("scored_at", rs.getString("scored_at"));
                row.addProperty("scored_at_display", rs.getString("scored_at_display"));
                rows.add(row);
                if (!latestByEquipment.has(equipmentId)) {
                    JsonObject latest = new JsonObject();
                    latest.addProperty("severity", severity);
                    latest.addProperty("confidence", confidence);
                    latestByEquipment.add(equipmentId, latest);
                }
            }

            double healthScore = computeHealthScore(latestByEquipment);
            out.add("recommendations", rows);
            out.addProperty("healthScore", String.format("%.1f%%", healthScore));
            out.addProperty("healthSubtext", healthBandLabel(healthScore));
            out.addProperty("ok", true);
            out.addProperty("message", "Recommendations refreshed");
        } catch (Exception e) {
            out.add("recommendations", rows);
            out.addProperty("healthScore", "0.0%");
            out.addProperty("healthSubtext", "DATA UNAVAILABLE");
            out.addProperty("ok", false);
            out.addProperty("message", "Refresh failed: " + e.getMessage());
            log.errorf("OperationsV2 refresh handler failed: %s", e.getMessage());
        }

        fireEvent(EVENT_REFRESH_RESULT, out);
    }

    private void handleTrend(JsonObject payload) {
        String datasource = getString(payload, "databaseConnection", "lakebase_historian");
        String equipmentId = getString(payload, "equipment_id", "");
        JsonObject out = new JsonObject();
        out.addProperty("equipment_id", equipmentId);
        JsonArray temperature = new JsonArray();
        JsonArray flow = new JsonArray();
        log.infof("OpsV2 trend requested: datasource=%s equipment_id=%s", datasource, equipmentId);

        if (equipmentId.isEmpty()) {
            out.add("temperature", temperature);
            out.add("flow", flow);
            out.addProperty("ok", false);
            out.addProperty("message", "Trend skipped: empty equipment_id");
            fireEvent(EVENT_TREND_RESULT, out);
            return;
        }
        try {
            String tempSql =
                "SELECT "
                    + "to_char(q.ts, 'YYYY-MM-DD HH24:MI:SS') AS t_label, "
                    + "q.metric_value "
                    + "FROM ( "
                    + "  SELECT s.timestamp AS ts, round(s.sensor_value::numeric, 2) AS metric_value "
                    + "  FROM public.sensor_data s "
                    + "  WHERE (trim(s.equipment_id) = trim(?) "
                    + "     OR replace(trim(s.equipment_id), '-', '_') = replace(trim(?), '-', '_')) "
                    + "    AND trim(lower(s.sensor_type)) IN ('temperature', 'temp') "
                    + "  ORDER BY s.timestamp DESC "
                    + "  LIMIT 120 "
                    + ") q "
                    + "ORDER BY q.ts ASC";

            String flowSql =
                "SELECT "
                    + "to_char(q.ts, 'YYYY-MM-DD HH24:MI:SS') AS t_label, "
                    + "q.metric_value "
                    + "FROM ( "
                    + "  SELECT s.timestamp AS ts, round(s.sensor_value::numeric, 2) AS metric_value "
                    + "  FROM public.sensor_data s "
                    + "  WHERE (trim(s.equipment_id) = trim(?) "
                    + "     OR replace(trim(s.equipment_id), '-', '_') = replace(trim(?), '-', '_')) "
                    + "    AND trim(lower(s.sensor_type)) IN ('flow_rate', 'flow') "
                    + "  ORDER BY s.timestamp DESC "
                    + "  LIMIT 120 "
                    + ") q "
                    + "ORDER BY q.ts ASC";

            int tempDsRows = 0;
            int flowDsRows = 0;
            StringBuilder tempCsv = new StringBuilder();
            StringBuilder flowCsv = new StringBuilder();

            try (SRConnection conn = RadGatewayHook.getGatewayContext().getDatasourceManager().getConnection(datasource)) {
                try (PreparedStatement ps = conn.prepareStatement(tempSql)) {
                    ps.setString(1, equipmentId);
                    ps.setString(2, equipmentId);
                    try (ResultSet rs = ps.executeQuery()) {
                        while (rs.next()) {
                            JsonObject p = new JsonObject();
                            p.addProperty("label", rs.getString("t_label"));
                            p.addProperty("value", rs.getString("metric_value"));
                            temperature.add(p);
                            if (tempCsv.length() > 0) {
                                tempCsv.append(",");
                            }
                            tempCsv.append(rs.getString("metric_value"));
                            tempDsRows++;
                        }
                    }
                }

                try (PreparedStatement ps = conn.prepareStatement(flowSql)) {
                    ps.setString(1, equipmentId);
                    ps.setString(2, equipmentId);
                    try (ResultSet rs = ps.executeQuery()) {
                        while (rs.next()) {
                            JsonObject p = new JsonObject();
                            p.addProperty("label", rs.getString("t_label"));
                            p.addProperty("value", rs.getString("metric_value"));
                            flow.add(p);
                            if (flowCsv.length() > 0) {
                                flowCsv.append(",");
                            }
                            flowCsv.append(rs.getString("metric_value"));
                            flowDsRows++;
                        }
                    }
                }
            }

            out.add("temperature", temperature);
            out.add("flow", flow);
            out.addProperty("temperatureJson", temperature.toString());
            out.addProperty("flowJson", flow.toString());
            out.addProperty("temperatureCsv", tempCsv.toString());
            out.addProperty("flowCsv", flowCsv.toString());
            out.addProperty("tempDsRows", tempDsRows);
            out.addProperty("flowDsRows", flowDsRows);
            out.addProperty("ok", true);
            out.addProperty(
                "message",
                "Trend refreshed (temp=" + temperature.size()
                    + ", flow=" + flow.size()
                    + ", ds=" + tempDsRows + "/" + flowDsRows + ")"
            );
            log.infof(
                "OpsV2 trend success: equipment_id=%s temp=%d flow=%d ds=%d/%d",
                equipmentId,
                temperature.size(),
                flow.size(),
                tempDsRows,
                flowDsRows
            );
        } catch (Exception e) {
            out.add("temperature", temperature);
            out.add("flow", flow);
            out.addProperty("temperatureJson", temperature.toString());
            out.addProperty("flowJson", flow.toString());
            out.addProperty("temperatureCsv", "");
            out.addProperty("flowCsv", "");
            out.addProperty("ok", false);
            out.addProperty("message", "Trend refresh failed: " + e.getMessage());
            log.errorf("OperationsV2 trend handler failed: %s", e.getMessage());
        }

        fireEvent(EVENT_TREND_RESULT, out);
    }

    private PyObject invokeGenieQuery(ScriptManager scriptManager, String question, String conversationId) throws Exception {
        // Use direct runCode in session scope to mirror Script Console behavior.
        PyObject globals = scriptManager.getGlobals();
        PyStringMap locals = scriptManager.createLocalsMap();
        locals.__setitem__("__question__", Py.java2py(question));
        locals.__setitem__("__conv__", Py.java2py(conversationId));
        scriptManager.runCode(
            "try:\n"
                + "    __result__ = genie.api.queryGenie(__question__, __conv__)\n"
                + "except Exception as e:\n"
                + "    __result__ = {\n"
                + "        'success': False,\n"
                + "        'response': 'Error: ' + str(e),\n"
                + "        'conversationId': __conv__\n"
                + "    }",
            globals,
            locals,
            "opsv2_genie_delegate"
        );
        PyObject result = locals.__finditem__("__result__");
        if (result == null || result == Py.None) {
            // Some script contexts may place assignments in globals.
            result = globals.__finditem__("__result__");
        }
        if (result == null || result == Py.None) {
            throw new Exception("genie.api.queryGenie returned no result.");
        }
        return result;
    }

    private String getString(JsonObject obj, String key, String defaultValue) {
        if (obj == null) {
            return defaultValue;
        }
        JsonElement el = obj.get(key);
        if (el == null || el.isJsonNull()) {
            return defaultValue;
        }
        try {
            return el.getAsString();
        } catch (Exception ex) {
            return defaultValue;
        }
    }

    private String normalizeDecision(String raw) {
        String d = raw == null ? "" : raw.trim().toLowerCase();
        if ("approved".equals(d) || "rejected".equals(d) || "deferred".equals(d)) {
            return d;
        }
        return "deferred";
    }

    private String getPyField(PyObject pyObj, String key, String defaultValue) {
        if (pyObj == null) {
            return defaultValue;
        }
        try {
            PyObject field = pyObj.__finditem__(key);
            if (field == null || field == Py.None) {
                return defaultValue;
            }
            Object asString = field.__tojava__(String.class);
            if (asString instanceof String) {
                return (String) asString;
            }
            return field.toString();
        } catch (Exception ex) {
            return defaultValue;
        }
    }

    private double computeHealthScore(JsonObject latestByEquipment) {
        if (latestByEquipment == null || latestByEquipment.size() == 0) {
            return 100.0;
        }

        double totalRisk = 0.0;
        int count = 0;
        for (String equipmentId : latestByEquipment.keySet()) {
            JsonObject row = latestByEquipment.getAsJsonObject(equipmentId);
            String severity = getString(row, "severity", "low").toLowerCase();
            String confidenceRaw = getString(row, "confidence", "0");
            double confidence;
            try {
                confidence = Double.parseDouble(confidenceRaw);
            } catch (Exception ignored) {
                confidence = 0.0;
            }
            confidence = Math.max(0.0, Math.min(1.0, confidence));

            double severityWeight;
            switch (severity) {
                case "critical":
                    severityWeight = 45.0;
                    break;
                case "high":
                    severityWeight = 28.0;
                    break;
                case "medium":
                    severityWeight = 16.0;
                    break;
                default:
                    severityWeight = 6.0;
                    break;
            }

            totalRisk += severityWeight * confidence;
            count += 1;
        }

        double avgRisk = totalRisk / Math.max(1, count);
        double health = 100.0 - avgRisk;
        return Math.max(0.0, Math.min(100.0, health));
    }

    private String healthBandLabel(double score) {
        if (score >= 90.0) {
            return "EXCELLENT STABILITY";
        }
        if (score >= 75.0) {
            return "OPERATIONAL EFFICIENCY";
        }
        if (score >= 60.0) {
            return "ELEVATED RISK";
        }
        return "CRITICAL ATTENTION";
    }

    @Override
    public void fireEvent(String eventName, JsonObject event) {
        // Explicitly route model delegate events back to the client-side ComponentStoreDelegate.
        this.component.fireEvent("model", eventName, event);
    }
}
