#!/bin/bash
# OpenCode Session Logger
# Usage: ./session-logger.sh [start|agent|metric|end|status]

LOG_DIR="$HOME/.config/opencode/logs"
SESSION_LOG="$LOG_DIR/session.log"
METRICS_LOG="$LOG_DIR/metrics.log"
AGENT_LOG="$LOG_DIR/agent-usage.log"

# Ensure log directory and files exist
mkdir -p "$LOG_DIR"
touch "$SESSION_LOG" "$METRICS_LOG" "$AGENT_LOG"

# Get session ID (use process ID as simple session identifier)
SESSION_ID="$$"

case "$1" in
  "start")
    echo "🚀 Starting OpenCode session logging..."
    echo "=== OpenCode Session Started ===" >> "$SESSION_LOG"
    echo "Session ID: $SESSION_ID" >> "$SESSION_LOG"
    echo "Start Time: $(date)" >> "$SESSION_LOG"
    echo "Working Directory: $(pwd)" >> "$SESSION_LOG"
    echo "User: $(whoami)" >> "$SESSION_LOG"
    
    # Detect project type
    if [ -f "package.json" ]; then
      PROJECT_TYPE="Web Application"
    elif [ -d "api" ] || [ -f "openapi.yaml" ]; then
      PROJECT_TYPE="API Service"
    elif [ -d "ios" ] || [ -d "android" ] || [ -f "pubspec.yaml" ]; then
      PROJECT_TYPE="Mobile Application"
    else
      PROJECT_TYPE="General Project"
    fi
    
    echo "Project Type: $PROJECT_TYPE" >> "$SESSION_LOG"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$SESSION_LOG"
    
    # Log session start metric
    echo "$(date +%s),session_start,$SESSION_ID,$PROJECT_TYPE" >> "$METRICS_LOG"
    
    echo "✅ Session logging started (ID: $SESSION_ID)"
    echo "📁 Logs location: $LOG_DIR"
    ;;
    
  "agent")
    AGENT_NAME="$2"
    TASK_DESCRIPTION="$3"
    
    if [ -z "$AGENT_NAME" ]; then
      echo "Usage: $0 agent <agent_name> [task_description]"
      exit 1
    fi
    
    TIMESTAMP=$(date)
    echo "🤖 Logging agent usage: $AGENT_NAME"
    
    # Log to session log
    echo "Agent Used: @$AGENT_NAME - $TIMESTAMP" >> "$SESSION_LOG"
    if [ -n "$TASK_DESCRIPTION" ]; then
      echo "  Task: $TASK_DESCRIPTION" >> "$SESSION_LOG"
    fi
    
    # Log to agent usage log
    echo "$TIMESTAMP,@$AGENT_NAME,$TASK_DESCRIPTION" >> "$AGENT_LOG"
    
    # Log metric
    echo "$(date +%s),agent_usage,$AGENT_NAME,$SESSION_ID" >> "$METRICS_LOG"
    
    echo "✅ Agent usage logged"
    ;;
    
  "metric")
    METRIC_TYPE="$2"
    METRIC_VALUE="$3"
    METRIC_UNIT="$4"
    
    if [ -z "$METRIC_TYPE" ] || [ -z "$METRIC_VALUE" ]; then
      echo "Usage: $0 metric <type> <value> [unit]"
      echo "Examples:"
      echo "  $0 metric response_time 2.5 seconds"
      echo "  $0 metric context_load_time 1.2 seconds"
      echo "  $0 metric token_usage 1500 tokens"
      exit 1
    fi
    
    TIMESTAMP=$(date +%s)
    echo "📊 Logging metric: $METRIC_TYPE = $METRIC_VALUE $METRIC_UNIT"
    
    # Log to metrics file
    echo "$TIMESTAMP,$METRIC_TYPE,$METRIC_VALUE,$METRIC_UNIT,$SESSION_ID" >> "$METRICS_LOG"
    
    # Log to session log
    echo "Metric: $METRIC_TYPE = $METRIC_VALUE $METRIC_UNIT - $(date)" >> "$SESSION_LOG"
    
    echo "✅ Metric logged"
    ;;
    
  "end")
    echo "🏁 Ending OpenCode session..."
    
    # Calculate session duration
    START_TIME=$(grep "Start Time:" "$SESSION_LOG" | tail -1 | cut -d: -f2- | xargs)
    if [ -n "$START_TIME" ]; then
      START_EPOCH=$(date -j -f "%a %b %d %H:%M:%S %Z %Y" "$START_TIME" +%s 2>/dev/null || echo "0")
      END_EPOCH=$(date +%s)
      DURATION=$((END_EPOCH - START_EPOCH))
      
      echo "Session Duration: ${DURATION}s" >> "$SESSION_LOG"
    fi
    
    echo "End Time: $(date)" >> "$SESSION_LOG"
    echo "=== Session Ended ===" >> "$SESSION_LOG"
    echo "" >> "$SESSION_LOG"
    
    # Log session end metric
    echo "$(date +%s),session_end,$SESSION_ID,$DURATION" >> "$METRICS_LOG"
    
    echo "✅ Session ended and logged"
    ;;
    
  "status")
    echo "📊 OpenCode Session Logging Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Show current session info
    if [ -f "$SESSION_LOG" ]; then
      LAST_SESSION=$(grep "Session ID:" "$SESSION_LOG" | tail -1)
      if [ -n "$LAST_SESSION" ]; then
        echo "🔄 Current Session: $LAST_SESSION"
      fi
    fi
    
    # Show log file sizes
    if [ -f "$SESSION_LOG" ]; then
      SESSION_SIZE=$(wc -l < "$SESSION_LOG" 2>/dev/null || echo "0")
      echo "📝 Session log entries: $SESSION_SIZE"
    fi
    
    if [ -f "$AGENT_LOG" ]; then
      AGENT_ENTRIES=$(wc -l < "$AGENT_LOG" 2>/dev/null || echo "0")
      echo "🤖 Agent usage entries: $AGENT_ENTRIES"
    fi
    
    if [ -f "$METRICS_LOG" ]; then
      METRIC_ENTRIES=$(wc -l < "$METRICS_LOG" 2>/dev/null || echo "0")
      echo "📊 Metric entries: $METRIC_ENTRIES"
    fi
    
    # Show recent agent usage
    if [ -f "$AGENT_LOG" ] && [ -s "$AGENT_LOG" ]; then
      echo ""
      echo "🤖 Recent Agent Usage:"
      tail -5 "$AGENT_LOG" | while IFS=',' read -r timestamp agent task; do
        echo "  • $agent - $timestamp"
      done
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ;;
    
  "report")
    echo "📈 OpenCode Session Report"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Agent usage summary
    if [ -f "$AGENT_LOG" ] && [ -s "$AGENT_LOG" ]; then
      echo "🤖 Most Used Agents:"
      cut -d',' -f2 "$AGENT_LOG" | sort | uniq -c | sort -nr | head -5 | while read -r count agent; do
        echo "  • $agent: $count times"
      done
      echo ""
    fi
    
    # Session statistics
    if [ -f "$METRICS_LOG" ] && [ -s "$METRICS_LOG" ]; then
      echo "📊 Session Statistics:"
      TOTAL_SESSIONS=$(grep "session_start" "$METRICS_LOG" | wc -l)
      echo "  • Total sessions: $TOTAL_SESSIONS"
      
      TOTAL_AGENT_CALLS=$(grep "agent_usage" "$METRICS_LOG" | wc -l)
      echo "  • Total agent calls: $TOTAL_AGENT_CALLS"
      
      if [ "$TOTAL_SESSIONS" -gt 0 ]; then
        AVG_CALLS=$((TOTAL_AGENT_CALLS / TOTAL_SESSIONS))
        echo "  • Average calls per session: $AVG_CALLS"
      fi
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ;;
    
  *)
    echo "OpenCode Session Logger"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start                    - Start session logging"
    echo "  agent <name> [task]      - Log agent usage"
    echo "  metric <type> <value>    - Log performance metric"
    echo "  end                      - End session logging"
    echo "  status                   - Show logging status"
    echo "  report                   - Generate usage report"
    echo ""
    echo "Examples:"
    echo "  $0 start                           # Start logging"
    echo "  $0 agent bmad-master \"Create PRD\" # Log agent usage"
    echo "  $0 metric response_time 2.5        # Log metric"
    echo "  $0 status                          # Check status"
    echo "  $0 end                             # End session"
    ;;
esac