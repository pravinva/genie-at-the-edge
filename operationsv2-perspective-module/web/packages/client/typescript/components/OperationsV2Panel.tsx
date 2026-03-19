import * as React from "react";
import {
    AbstractUIElementStore,
    Component,
    ComponentMeta,
    ComponentProps,
    ComponentStoreDelegate,
    JsObject,
    makeLogger,
    PComponent,
    PropertyTree,
    SizeObject
} from "@inductiveautomation/perspective-client";

export const COMPONENT_TYPE = "ops.display.operationsv2";

interface EquipmentStatus {
    equipmentId: string;
    status: string;
}

interface RecommendationRow {
    equipment_id: string;
    severity: string;
    anomaly_score?: string | number;
    confidence: string | number;
    recommendation_text: string;
    estimated_ttf: string | number;
    scored_at?: string;
    scored_at_display: string;
}

interface TrendPoint {
    label: string;
    value: number;
}

interface EquipmentTrend {
    temperature: TrendPoint[];
    flow: TrendPoint[];
}

type ChatRole = "operator" | "genie" | "system";

interface ChatTurn {
    role: ChatRole;
    text: string;
}

interface ParsedTable {
    headers: string[];
    rows: string[][];
}

const GENIE_SAMPLE_QUESTIONS: string[] = [
    "What is the status of REACTOR_02 right now?",
    "Show severity and confidence for all equipment in a table.",
    "Which equipment is critical right now?",
    "What maintenance action is recommended for PUMP_07?"
];

interface OperationsV2Props {
    title: string;
    siteLabel: string;
    equipmentStatuses: EquipmentStatus[];
    healthScore: string;
    healthSubtext: string;
    recommendations: RecommendationRow[];
    trendData: {
        [key: string]: EquipmentTrend;
    };
    genieTranscript: string;
    genieConversationId: string;
    genieBusy: boolean;
    showSqlButton: boolean;
    databaseConnection: string;
    operatorId: string;
}

interface OperationsV2DelegateState {
    busy: boolean;
    transcript: string;
    conversationId: string;
    lastMessage: string;
    latestSql: string;
    latestTableMarkdown: string;
    recommendations: RecommendationRow[];
    trendData: { [key: string]: EquipmentTrend };
    healthScore: string;
    healthSubtext: string;
    trendStatus: string;
}

interface OperationsV2State {
    selectedIndex: number;
    genieInput: string;
    localTranscript: string;
    showSqlPanel: boolean;
}

enum OpsV2Events {
    DECISION = "opsv2-decision-event",
    DECISION_RESULT = "opsv2-decision-result-event",
    GENIE_ASK = "opsv2-genie-ask-event",
    GENIE_CLEAR = "opsv2-genie-clear-event",
    GENIE_RESULT = "opsv2-genie-result-event",
    REFRESH = "opsv2-refresh-event",
    REFRESH_RESULT = "opsv2-refresh-result-event",
    TREND = "opsv2-trend-event",
    TREND_RESULT = "opsv2-trend-result-event"
}

const logger = makeLogger("operationsv2.panel");

const unwrapValue = (v: any): any => {
    if (v && typeof v === "object" && "value" in v) {
        return (v as any).value;
    }
    return v;
};

const normalizeEquipmentKey = (v: any): string => {
    return String(unwrapValue(v) ?? "")
        .trim()
        .toUpperCase()
        .replace(/-/g, "_");
};

const toRecommendationRows = (raw: any): RecommendationRow[] => {
    const rows: any[] = [];

    if (Array.isArray(raw)) {
        rows.push(...raw);
    } else if (raw && typeof raw === "object") {
        const v = unwrapValue(raw);
        if (Array.isArray(v)) {
            rows.push(...v);
        } else {
            const keys = Object.keys(v || {}).filter(k => /^\d+$/.test(k)).sort((a, b) => Number(a) - Number(b));
            if (keys.length) {
                keys.forEach(k => rows.push((v as any)[k]));
            }
        }
    }

    return rows
        .map(r => unwrapValue(r))
        .filter(r => r && typeof r === "object")
        .map(r => ({
            equipment_id: String(unwrapValue((r as any).equipment_id) ?? ""),
            severity: String(unwrapValue((r as any).severity) ?? ""),
            anomaly_score: String(unwrapValue((r as any).anomaly_score) ?? ""),
            confidence: String(unwrapValue((r as any).confidence) ?? ""),
            recommendation_text: String(unwrapValue((r as any).recommendation_text) ?? ""),
            estimated_ttf: String(unwrapValue((r as any).estimated_ttf) ?? ""),
            scored_at: String(unwrapValue((r as any).scored_at) ?? ""),
            scored_at_display: String(unwrapValue((r as any).scored_at_display) ?? "")
        }));
};

class OperationsV2GatewayDelegate extends ComponentStoreDelegate {
    private busy = false;
    private transcript = "GENIE: Ready.";
    private conversationId = "";
    private lastMessage = "";
    private latestSql = "";
    private latestTableMarkdown = "";
    private recommendations: RecommendationRow[] = [];
    private trendData: { [key: string]: EquipmentTrend } = {};
    private healthScore = "";
    private healthSubtext = "";
    private trendStatus = "";

    constructor(componentStore: AbstractUIElementStore) {
        super(componentStore);
    }

    mapStateToProps(): OperationsV2DelegateState {
        return {
            busy: this.busy,
            transcript: this.transcript,
            conversationId: this.conversationId,
            lastMessage: this.lastMessage,
            latestSql: this.latestSql,
            latestTableMarkdown: this.latestTableMarkdown,
            recommendations: this.recommendations,
            trendData: this.trendData,
            healthScore: this.healthScore,
            healthSubtext: this.healthSubtext,
            trendStatus: this.trendStatus
        };
    }

    fireDecision(payload: JsObject): void {
        this.busy = true;
        this.notify();
        this.fireEvent(OpsV2Events.DECISION, payload);
    }

    fireGenieAsk(payload: JsObject): void {
        this.busy = true;
        this.lastMessage = "Querying Genie... this can take up to 20s.";
        this.notify();
        this.fireEvent(OpsV2Events.GENIE_ASK, payload);
    }

    fireGenieClear(): void {
        this.busy = false;
        this.transcript = "GENIE: Ready.";
        this.conversationId = "";
        this.lastMessage = "Chat cleared";
        this.latestSql = "";
        this.latestTableMarkdown = "";
        this.notify();
        this.fireEvent(OpsV2Events.GENIE_CLEAR, {});
    }

    fireRefresh(payload: JsObject): void {
        this.fireEvent(OpsV2Events.REFRESH, payload);
    }

    fireTrend(payload: JsObject): void {
        this.fireEvent(OpsV2Events.TREND, payload);
    }

    handleEvent(eventName: string, eventObject: JsObject): void {
        if (eventName === OpsV2Events.DECISION_RESULT) {
            this.busy = false;
            this.lastMessage = String(eventObject && eventObject.message ? eventObject.message : "");
            this.notify();
            return;
        }

        if (eventName === OpsV2Events.GENIE_RESULT) {
            this.busy = Boolean(eventObject && eventObject.busy);
            this.transcript = String(eventObject && eventObject.transcript ? eventObject.transcript : this.transcript);
            this.conversationId = String(eventObject && eventObject.conversationId ? eventObject.conversationId : this.conversationId);
            this.lastMessage = String(eventObject && eventObject.message ? eventObject.message : "");
            this.latestSql = String(eventObject && eventObject.sql ? eventObject.sql : this.latestSql);
            this.latestTableMarkdown = String(eventObject && eventObject.tableMarkdown ? eventObject.tableMarkdown : this.latestTableMarkdown);
            this.notify();
            return;
        }

        if (eventName === OpsV2Events.REFRESH_RESULT) {
            this.recommendations = toRecommendationRows(eventObject && (eventObject as any).recommendations);
            this.healthScore = String((eventObject && (eventObject as any).healthScore) || this.healthScore || "");
            this.healthSubtext = String((eventObject && (eventObject as any).healthSubtext) || this.healthSubtext || "");
            const baseMessage = String(eventObject && eventObject.message ? eventObject.message : "Refresh completed");
            this.lastMessage = `${baseMessage} (${this.recommendations.length} rows)`;
            logger.info(() => `OpsV2 refresh rows received: ${this.recommendations.length}`);
            this.notify();
            return;
        }

        if (eventName === OpsV2Events.TREND_RESULT) {
            const evt = unwrapValue(eventObject) || {};
            const equipmentId = normalizeEquipmentKey((evt as any).equipment_id);
            if (equipmentId) {
                const temperatureFromCsv = toTrendPointsFromCsv((evt as any).temperatureCsv);
                const flowFromCsv = toTrendPointsFromCsv((evt as any).flowCsv);
                const temperatureFromJson = toTrendPointsFromJson((evt as any).temperatureJson);
                const flowFromJson = toTrendPointsFromJson((evt as any).flowJson);
                const temperature = temperatureFromCsv.length
                    ? temperatureFromCsv
                    : temperatureFromJson.length
                    ? temperatureFromJson
                    : toTrendPoints((evt as any).temperature);
                const flow = flowFromCsv.length
                    ? flowFromCsv
                    : flowFromJson.length
                    ? flowFromJson
                    : toTrendPoints((evt as any).flow);
                this.trendData = {
                    ...this.trendData,
                    [equipmentId]: { temperature, flow }
                };
                this.trendStatus = String((evt as any).message || "");
                this.lastMessage = this.trendStatus || this.lastMessage;
                logger.info(() => `OpsV2 trend received for ${equipmentId}: temp=${temperature.length}, flow=${flow.length}`);
                this.notify();
            } else {
                logger.warn(() => "OpsV2 trend result ignored: missing equipment_id");
            }
            return;
        }

        logger.warn(() => `Unhandled delegate event '${eventName}'`);
    }
}

const statusClass = (status: string): string => {
    const s = (status || "").toLowerCase();
    if (s === "critical") {
        return "critical";
    }
    if (s === "high" || s === "warning") {
        return "high";
    }
    if (s === "medium") {
        return "medium";
    }
    return "healthy";
};

const severityRank = (s: string): number => {
    const v = (s || "").toLowerCase();
    if (v === "critical") return 4;
    if (v === "high") return 3;
    if (v === "medium") return 2;
    if (v === "low") return 1;
    return 0;
};

const toLeftRailStatuses = (rows: RecommendationRow[], fallback: EquipmentStatus[]): EquipmentStatus[] => {
    if (!rows.length) {
        return fallback || [];
    }

    const byEquipment: { [equipmentId: string]: EquipmentStatus } = {};
    rows.forEach(r => {
        const equipmentId = String(r.equipment_id || "").trim();
        if (!equipmentId) {
            return;
        }
        const status = statusClass(String(r.severity || ""));
        const current = byEquipment[equipmentId];
        if (!current || severityRank(status) > severityRank(current.status)) {
            byEquipment[equipmentId] = { equipmentId, status };
        }
    });

    return Object.keys(byEquipment)
        .sort((a, b) => a.localeCompare(b))
        .map(k => byEquipment[k]);
};

const toTrendPoints = (raw: any): TrendPoint[] => {
    const rows: any[] = [];

    if (Array.isArray(raw)) {
        rows.push(...raw);
    } else if (raw && typeof raw === "object") {
        const v = unwrapValue(raw);
        if (Array.isArray(v)) {
            rows.push(...v);
        } else {
            const keys = Object.keys(v || {}).filter(k => /^\d+$/.test(k)).sort((a, b) => Number(a) - Number(b));
            if (keys.length) {
                keys.forEach(k => rows.push((v as any)[k]));
            }
        }
    }

    return rows
        .map(r => unwrapValue(r))
        .filter(r => r && typeof r === "object")
        .map(r => ({
            label: String(unwrapValue((r as any).label) ?? ""),
            value: Number(unwrapValue((r as any).value) ?? 0)
        }))
        .filter(p => p.label.length > 0 && Number.isFinite(p.value));
};

const toTrendPointsFromJson = (raw: any): TrendPoint[] => {
    try {
        const unwrapDeep = (v: any): any => {
            let out = v;
            for (let i = 0; i < 4; i += 1) {
                if (out && typeof out === "object" && "value" in out) {
                    out = (out as any).value;
                    continue;
                }
                break;
            }
            return out;
        };

        let v = unwrapDeep(raw);
        if (v == null) {
            return [];
        }

        if (typeof v === "string") {
            const s = v.trim();
            if (!s) {
                return [];
            }
            let parsed: any = JSON.parse(s);
            if (typeof parsed === "string") {
                parsed = JSON.parse(parsed);
            }
            return toTrendPoints(parsed);
        }

        return toTrendPoints(v);
    } catch (_e) {
        return [];
    }
};

const toTrendPointsFromCsv = (raw: any): TrendPoint[] => {
    const s = String(unwrapValue(raw) ?? "").trim();
    if (!s) {
        return [];
    }
    return s
        .split(",")
        .map((v, i) => ({
            label: String(i + 1),
            value: Number(v)
        }))
        .filter(p => Number.isFinite(p.value));
};

const parseTranscriptTurns = (transcriptRaw: string): ChatTurn[] => {
    const text = String(transcriptRaw || "").trim();
    if (!text) {
        return [];
    }

    const lines = text.split(/\r?\n/);
    const turns: ChatTurn[] = [];
    let currentRole: ChatRole | null = null;
    let buffer: string[] = [];

    const flush = () => {
        if (currentRole && buffer.length) {
            turns.push({
                role: currentRole,
                text: buffer.join("\n").trim()
            });
        }
        buffer = [];
    };

    lines.forEach(line => {
        if (line.startsWith("OPERATOR:")) {
            flush();
            currentRole = "operator";
            buffer.push(line.replace(/^OPERATOR:\s*/, ""));
            return;
        }
        if (line.startsWith("GENIE:")) {
            flush();
            currentRole = "genie";
            buffer.push(line.replace(/^GENIE:\s*/, ""));
            return;
        }
        if (!currentRole) {
            currentRole = "system";
        }
        buffer.push(line);
    });
    flush();

    return turns.filter(t => t.text.length > 0);
};

const parseMarkdownTable = (markdown: string): ParsedTable | null => {
    const text = String(markdown || "").trim();
    if (!text) {
        return null;
    }
    const lines = text
        .split(/\r?\n/)
        .map(l => l.trim())
        .filter(l => l.startsWith("|") && l.endsWith("|"));
    if (lines.length < 2) {
        return null;
    }
    const splitRow = (line: string): string[] =>
        line
            .slice(1, -1)
            .split("|")
            .map(c => c.trim());

    const headers = splitRow(lines[0]);
    const rows = lines
        .slice(2)
        .map(splitRow)
        .filter(r => r.length === headers.length);

    if (!headers.length || !rows.length) {
        return null;
    }
    return { headers, rows };
};

class MiniTrend extends React.PureComponent<{ title: string; points: TrendPoint[] }> {
    render() {
        const points = this.props.points || [];
        const width = 420;
        const height = 140;
        const chartLeft = 42;
        const chartRight = 12;
        const chartTop = 10;
        const chartBottom = 28;
        const plotWidth = width - chartLeft - chartRight;
        const plotHeight = height - chartTop - chartBottom;

        if (!points.length) {
            return (
                <div className="opsv2-trend-card">
                    <div className="opsv2-card-title">{this.props.title}</div>
                    <div className="opsv2-empty">No trend data</div>
                </div>
            );
        }

        const values = points.map(p => Number(p.value || 0));
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = Math.max(1, max - min);
        const fmtX = (raw: string): string => {
            const s = String(raw || "");
            const match = s.match(/(\d{2}:\d{2})(:\d{2})?/);
            return match ? match[1] : s;
        };
        const firstLabel = String(points[0]?.label || "");
        const lastLabel = String(points[points.length - 1]?.label || "");
        const hasTimeLabels = /(\d{2}:\d{2})/.test(firstLabel) || /(\d{2}:\d{2})/.test(lastLabel);
        const xStart = hasTimeLabels ? fmtX(firstLabel) : "Older";
        const xEnd = hasTimeLabels ? fmtX(lastLabel) : "Latest";
        const isTemperature = this.props.title.toLowerCase().includes("temperature");
        const chartId = this.props.title.replace(/[^a-zA-Z0-9]+/g, "_").toLowerCase();

        const toXY = (value: number, idx: number): string => {
            const x = chartLeft + (idx * plotWidth) / Math.max(1, points.length - 1);
            const y = chartTop + (1 - (value - min) / range) * plotHeight;
            return `${x},${y}`;
        };

        const polyline = values.map((v, i) => toXY(v, i)).join(" ");
        const areaPoints = `${chartLeft},${chartTop + plotHeight} ${polyline} ${chartLeft + plotWidth},${chartTop + plotHeight}`;

        return (
            <div className="opsv2-trend-card">
                <div className="opsv2-card-title">{this.props.title}</div>
                <div className="opsv2-trend-plot-wrap">
                    <svg className="opsv2-trend-svg" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
                        <defs>
                            <linearGradient id={`${chartId}-plot-bg`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#f8fcff" />
                                <stop offset="100%" stopColor="#e6f1fb" />
                            </linearGradient>
                            <linearGradient id={`${chartId}-area`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor={isTemperature ? "rgba(220, 38, 38, 0.28)" : "rgba(15, 118, 110, 0.30)"} />
                                <stop offset="100%" stopColor={isTemperature ? "rgba(220, 38, 38, 0.03)" : "rgba(15, 118, 110, 0.02)"} />
                            </linearGradient>
                        </defs>
                        <rect
                            className="opsv2-plot-area"
                            x={chartLeft}
                            y={chartTop}
                            width={plotWidth}
                            height={plotHeight}
                            fill={`url(#${chartId}-plot-bg)`}
                        />
                        <line className="opsv2-grid" x1={chartLeft} y1={chartTop} x2={width - chartRight} y2={chartTop} />
                        <line className="opsv2-grid" x1={chartLeft} y1={chartTop + plotHeight / 2} x2={width - chartRight} y2={chartTop + plotHeight / 2} />
                        <line className="opsv2-grid" x1={chartLeft} y1={chartTop + plotHeight} x2={width - chartRight} y2={chartTop + plotHeight} />
                        <line className="opsv2-axis" x1={chartLeft} y1={chartTop} x2={chartLeft} y2={chartTop + plotHeight} />
                        <line className="opsv2-axis" x1={chartLeft} y1={chartTop + plotHeight} x2={width - chartRight} y2={chartTop + plotHeight} />
                        <polygon className="opsv2-trend-area" points={areaPoints} fill={`url(#${chartId}-area)`} />
                        <polyline className={`opsv2-trend-line ${isTemperature ? "temperature" : "flow"}`} points={polyline} />
                    </svg>
                    <div className="opsv2-trend-y-overlay">
                        <span className="opsv2-trend-y-title">Value</span>
                        <span className="opsv2-trend-y-max">{max.toFixed(1)}</span>
                        <span className="opsv2-trend-y-min">{min.toFixed(1)}</span>
                    </div>
                </div>
                <div className="opsv2-trend-legend">
                    <div className="opsv2-trend-x-legend">
                        <span>{xStart}</span>
                        <span className="opsv2-trend-axis-title">Time</span>
                        <span>{xEnd}</span>
                    </div>
                </div>
            </div>
        );
    }
}

export class OperationsV2Panel extends Component<ComponentProps<OperationsV2Props, OperationsV2DelegateState>, OperationsV2State> {
    private refreshTimer: number | undefined;

    state: OperationsV2State = {
        selectedIndex: 0,
        genieInput: "",
        localTranscript: "",
        showSqlPanel: false
    };

    componentDidMount() {
        this.requestRefresh();
        this.refreshTimer = window.setInterval(() => this.requestRefresh(), 15000);
    }

    componentWillUnmount() {
        if (this.refreshTimer !== undefined) {
            window.clearInterval(this.refreshTimer);
            this.refreshTimer = undefined;
        }
    }

    componentDidUpdate(prevProps: ComponentProps<OperationsV2Props>) {
        if (prevProps.props.genieTranscript !== this.props.props.genieTranscript) {
            this.setState({ localTranscript: this.props.props.genieTranscript || "" });
        }
        if (prevProps.props.recommendations !== this.props.props.recommendations) {
            this.setState({ selectedIndex: 0 });
        }
        const prevDelegateRows = (prevProps.delegate && prevProps.delegate.recommendations) || [];
        const currDelegateRows = (this.props.delegate && this.props.delegate.recommendations) || [];
        if (prevDelegateRows !== currDelegateRows && currDelegateRows.length > 0) {
            const first = currDelegateRows[0];
            if (first && first.equipment_id) {
                this.requestTrend(first.equipment_id);
            }
        }
    }

    private getSelected(): RecommendationRow | undefined {
        const rows = this.getRows();
        if (!rows.length) {
            return undefined;
        }
        const idx = Math.max(0, Math.min(this.state.selectedIndex, rows.length - 1));
        return rows[idx];
    }

    private getRows(): RecommendationRow[] {
        const delegateRows = this.props.delegate && this.props.delegate.recommendations;
        if (delegateRows && delegateRows.length) {
            return delegateRows;
        }
        return this.props.props.recommendations || [];
    }

    private getTrendForSelected(): EquipmentTrend {
        const selected = this.getSelected();
        const key = selected ? normalizeEquipmentKey(selected.equipment_id) : "";
        const delegateTrend = this.props.delegate && this.props.delegate.trendData;
        const trend = ((delegateTrend || this.props.props.trendData || {}) as any)[key];
        return trend || { temperature: [], flow: [] };
    }

    private onSelectRow(idx: number) {
        const rows = this.getRows();
        const row = rows[idx];
        this.setState({ selectedIndex: idx });
        if (row && row.equipment_id) {
            this.requestTrend(row.equipment_id);
        }
    }

    private requestRefresh() {
        if (!this.props.store.delegate) {
            return;
        }
        const delegate = this.props.store.delegate as OperationsV2GatewayDelegate;
        delegate.fireRefresh({
            databaseConnection: this.props.props.databaseConnection || "lakebase_historian"
        });
    }

    private requestTrend(equipmentId: string) {
        const trimmed = String(equipmentId || "").trim();
        if (!this.props.store.delegate || !trimmed) {
            return;
        }
        const delegate = this.props.store.delegate as OperationsV2GatewayDelegate;
        delegate.fireTrend({
            equipment_id: trimmed,
            databaseConnection: this.props.props.databaseConnection || "lakebase_historian"
        });
    }

    private onDecision(decision: "approved" | "deferred" | "rejected") {
        const selected = this.getSelected();
        if (!selected || !this.props.store.delegate) {
            return;
        }
        const delegate = this.props.store.delegate as OperationsV2GatewayDelegate;
        delegate.fireDecision({
            decision: decision,
            equipment_id: selected.equipment_id || "",
            scored_at: selected.scored_at || selected.scored_at_display || "",
            operator_id: this.props.props.operatorId || "operator",
            feedback_text: `${decision} from OperationsV2 component`,
            databaseConnection: this.props.props.databaseConnection || "lakebase_historian"
        });
        window.setTimeout(() => this.requestRefresh(), 500);
    }

    private onAsk() {
        const input = (this.state.genieInput || "").trim();
        if (!input || !this.props.store.delegate) {
            return;
        }
        const delegate = this.props.store.delegate as OperationsV2GatewayDelegate;
        const current = this.props.delegate ? this.props.delegate.transcript : (this.state.localTranscript || this.props.props.genieTranscript || "GENIE: Ready.");
        delegate.fireGenieAsk({
            question: input,
            transcript: current,
            conversationId: (this.props.delegate && this.props.delegate.conversationId) || this.props.props.genieConversationId || ""
        });
        this.setState({ genieInput: "" });
    }

    private onClearChat() {
        if (this.props.store.delegate) {
            (this.props.store.delegate as OperationsV2GatewayDelegate).fireGenieClear();
        }
        this.setState({ genieInput: "", localTranscript: "GENIE: Ready.", showSqlPanel: false });
    }

    private onToggleSql() {
        this.setState({ showSqlPanel: !this.state.showSqlPanel });
    }

    render() {
        const p = this.props.props;
        const rows = this.getRows();
        const selected = this.getSelected();
        const trend = this.getTrendForSelected();
        const leftRailStatuses = toLeftRailStatuses(rows, p.equipmentStatuses || []);
        const transcript = (this.props.delegate && this.props.delegate.transcript)
            || this.state.localTranscript
            || p.genieTranscript
            || "GENIE: Ready.";
        const busy = (this.props.delegate && this.props.delegate.busy) || p.genieBusy;
        const lastMessage = (this.props.delegate && this.props.delegate.lastMessage) || "";
        const latestSql = (this.props.delegate && this.props.delegate.latestSql) || "";
        const latestTableMarkdown = (this.props.delegate && this.props.delegate.latestTableMarkdown) || "";
        const showSql = p.showSqlButton && this.state.showSqlPanel && !!latestSql;
        const healthScore = (this.props.delegate && this.props.delegate.healthScore) || p.healthScore;
        const healthSubtext = (this.props.delegate && this.props.delegate.healthSubtext) || p.healthSubtext;
        const trendStatus = (this.props.delegate && this.props.delegate.trendStatus) || "";
        const recSeverity = ((selected && selected.severity) || "low").toLowerCase();
        const chatTurns = parseTranscriptTurns(transcript);
        const parsedTable = parseMarkdownTable(latestTableMarkdown);

        return (
            <div {...this.props.emit({ classes: ["opsv2-root"] })}>
                <div className="opsv2-topbar">
                    <div className="opsv2-topbar-title">{p.title}</div>
                    <div className="opsv2-topbar-site">{p.siteLabel}</div>
                </div>

                <div className="opsv2-body">
                    <div className="opsv2-left">
                        <div className="opsv2-rail-header">EQUIPMENT STATUS</div>
                        {leftRailStatuses.map((s, i) => (
                            <div className="opsv2-eq-row" key={`${s.equipmentId}-${i}`}>
                                <span className={`opsv2-dot ${statusClass(s.status)}`} />
                                <span className="opsv2-eq-text">{s.equipmentId}</span>
                            </div>
                        ))}
                        <div className="opsv2-health-header">AI HEALTH SCORE</div>
                        <div className="opsv2-health-value">{healthScore}</div>
                        <div className="opsv2-health-sub">{healthSubtext}</div>
                    </div>

                    <div className="opsv2-center">
                        <MiniTrend title={`TEMPERATURE TREND (C) - ${selected ? selected.equipment_id : "N/A"}`} points={trend.temperature} />
                        <MiniTrend title={`COOLING FLOW TREND (L/min) - ${selected ? selected.equipment_id : "N/A"}`} points={trend.flow} />

                        <div className={`opsv2-rec-card severity-${recSeverity}`}>
                            <div className="opsv2-rec-header">
                                {selected ? `${(selected.severity || "").toUpperCase()} - AI RECOMMENDATION` : "AI RECOMMENDATION"}
                            </div>
                            <div className="opsv2-rec-summary">
                                <div className="opsv2-rec-counts">
                                    Rows: {rows.length} | Trend points (temp/flow): {trend.temperature.length}/{trend.flow.length}
                                </div>
                                {trendStatus ? <div className="opsv2-rec-counts">Trend status: {trendStatus}</div> : null}
                                <div className="opsv2-rec-title">{selected ? selected.equipment_id : "Select a recommendation row"}</div>
                                <div className="opsv2-rec-body">{selected ? selected.recommendation_text : "Recommendation details will appear here."}</div>
                                <div className="opsv2-rec-meta">
                                    {selected
                                        ? `Anomaly Score: ${selected.anomaly_score || "n/a"} | Confidence: ${selected.confidence} | TTF: ${selected.estimated_ttf} min | Scored: ${selected.scored_at_display}`
                                        : "Confidence | TTF | Scored At"}
                                </div>
                            </div>

                            <div className="opsv2-rec-table-wrap">
                                <table className="opsv2-rec-table">
                                    <thead>
                                        <tr>
                                            <th>equipment_id</th>
                                            <th>severity</th>
                                            <th>anomaly_score</th>
                                            <th>confidence</th>
                                            <th>estimated_ttf</th>
                                            <th>scored_at</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {rows.map((r, idx) => (
                                            <tr key={`${r.equipment_id}-${idx}`} className={idx === this.state.selectedIndex ? "selected" : ""} onClick={() => this.onSelectRow(idx)}>
                                                <td>{r.equipment_id}</td>
                                                <td>{r.severity}</td>
                                                <td>{r.anomaly_score}</td>
                                                <td>{r.confidence}</td>
                                                <td>{r.estimated_ttf}</td>
                                                <td>{r.scored_at_display}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            <div className="opsv2-actions">
                                <button className="opsv2-btn approve" disabled={!selected || busy} onClick={() => this.onDecision("approved")}>APPROVE</button>
                                <button className="opsv2-btn defer" disabled={!selected || busy} onClick={() => this.onDecision("deferred")}>DEFER</button>
                                <button className="opsv2-btn reject" disabled={!selected || busy} onClick={() => this.onDecision("rejected")}>REJECT</button>
                            </div>
                        </div>
                    </div>

                    <div className="opsv2-right">
                        <div className="opsv2-right-header">GENIE ASSISTANT</div>
                        <textarea
                            className="opsv2-genie-input"
                            value={this.state.genieInput}
                            placeholder="Ask Genie..."
                            onChange={e => this.setState({ genieInput: e.currentTarget.value })}
                        />
                        <div className="opsv2-sample-wrap">
                            <div className="opsv2-sample-title">Try a sample question</div>
                            <div className="opsv2-sample-list">
                                {GENIE_SAMPLE_QUESTIONS.map((q, idx) => (
                                    <button
                                        key={`sample-${idx}`}
                                        className="opsv2-sample-chip"
                                        type="button"
                                        onClick={() => this.setState({ genieInput: q })}
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="opsv2-genie-actions">
                            <button className="opsv2-btn ask" disabled={busy} onClick={() => this.onAsk()}>
                                {busy ? "ASKING..." : "ASK"}
                            </button>
                            <button className="opsv2-btn clear" onClick={() => this.onClearChat()}>
                                CLEAR
                            </button>
                            {p.showSqlButton ? (
                                <button className="opsv2-btn sql" disabled={!latestSql} onClick={() => this.onToggleSql()}>
                                    {this.state.showSqlPanel ? "HIDE SQL" : "SHOW SQL"}
                                </button>
                            ) : null}
                        </div>
                        {busy ? <div className="opsv2-processing">Processing query...</div> : null}
                        <div className="opsv2-genie-block">
                            {chatTurns.length ? chatTurns.map((turn, idx) => (
                                <div className={`opsv2-chat-turn ${turn.role}`} key={`chat-${idx}`}>
                                    <div className="opsv2-chat-role">{turn.role === "operator" ? "OPERATOR" : turn.role === "genie" ? "GENIE" : "SYSTEM"}</div>
                                    <div className="opsv2-chat-text">{turn.text}</div>
                                </div>
                            )) : <div className="opsv2-empty">No chat yet.</div>}
                        </div>
                        {parsedTable ? (
                            <div className="opsv2-genie-table-card">
                                <div className="opsv2-card-title">DATA TABLE</div>
                                <div className="opsv2-genie-table-wrap">
                                    <table className="opsv2-genie-table">
                                        <thead>
                                            <tr>
                                                {parsedTable.headers.map((h, i) => <th key={`h-${i}`}>{h}</th>)}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {parsedTable.rows.map((row, rIdx) => (
                                                <tr key={`r-${rIdx}`}>
                                                    {row.map((cell, cIdx) => <td key={`c-${rIdx}-${cIdx}`}>{cell}</td>)}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ) : null}
                        {showSql ? <pre className="opsv2-sql-block">{latestSql}</pre> : null}
                        {lastMessage ? <div className="opsv2-status">{lastMessage}</div> : null}
                    </div>
                </div>
            </div>
        );
    }
}

export class OperationsV2PanelMeta implements ComponentMeta {
    getComponentType(): string {
        return COMPONENT_TYPE;
    }

    getViewComponent(): PComponent {
        return OperationsV2Panel;
    }

    getDefaultSize(): SizeObject {
        return {
            width: 1280,
            height: 820
        };
    }

    createDelegate(component: AbstractUIElementStore): ComponentStoreDelegate | undefined {
        return new OperationsV2GatewayDelegate(component);
    }

    getPropsReducer(tree: PropertyTree): OperationsV2Props {
        return {
            title: tree.readString("title", "MAIN OPERATIONS VIEW - INTELLIGENT OPERATIONS PLATFORM"),
            siteLabel: tree.readString("siteLabel", "PLANT-01 | UTC"),
            equipmentStatuses: tree.read("equipmentStatuses", []),
            healthScore: tree.readString("healthScore", "87.3%"),
            healthSubtext: tree.readString("healthSubtext", "OPERATIONAL EFFICIENCY"),
            recommendations: tree.read("recommendations", []),
            trendData: tree.read("trendData", {}),
            genieTranscript: tree.readString("genieTranscript", "GENIE: Ready."),
            genieConversationId: tree.readString("genieConversationId", ""),
            genieBusy: tree.read("genieBusy", false),
            showSqlButton: tree.read("showSqlButton", true),
            databaseConnection: tree.readString("databaseConnection", "lakebase_historian"),
            operatorId: tree.readString("operatorId", "operator")
        };
    }
}
