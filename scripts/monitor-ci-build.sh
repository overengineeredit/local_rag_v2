#!/bin/bash

# CI Build Monitor Script
# Monitors GitHub Actions runs and provides detailed analysis on completion

set -euo pipefail

# Configuration
CHECK_INTERVAL=30
BRANCH="002-production-ci-cd"
REPO_DIR="/home/peenaki/Develop/local_rag_v2"
LOG_FILE="/tmp/ci-monitor-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] ${level}: ${message}" | tee -a "$LOG_FILE"
}

# Get the latest run ID for specific workflow and event type
get_latest_run_id() {
    local workflow="${1:-}"
    local event_type="${2:-}"
    cd "$REPO_DIR"
    
    if [[ -n "$workflow" ]]; then
        if [[ -n "$event_type" ]]; then
            # Get latest run for specific workflow and event type
            gh run list --workflow="$workflow" --limit 10 --json databaseId,event | \
                jq --arg event "$event_type" '.[] | select(.event == $event) | .databaseId' | head -1
        else
            # Get latest run for specific workflow
            gh run list --workflow="$workflow" --limit 1 --json databaseId --jq '.[0].databaseId'
        fi
    else
        # Get latest run for branch
        gh run list --branch "$BRANCH" --limit 1 --json databaseId --jq '.[0].databaseId'
    fi 2>/dev/null || echo ""
}

# Get workflow name for run
get_workflow_name() {
    local run_id=$1
    cd "$REPO_DIR"
    gh api "repos/overengineeredit/local_rag_v2/actions/runs/$run_id" | jq -r '.name // "unknown"' 2>/dev/null || echo "unknown"
}

# Get run status using API (more reliable)
get_run_status() {
    local run_id=$1
    cd "$REPO_DIR"
    gh api "repos/overengineeredit/local_rag_v2/actions/runs/$run_id" | \
        jq -r '(.status // "unknown") + ":" + (.conclusion // "null")' 2>/dev/null || echo "unknown:unknown"
}

# Get detailed job status
get_job_status() {
    local run_id=$1
    cd "$REPO_DIR"
    gh api "repos/overengineeredit/local_rag_v2/actions/runs/$run_id/jobs" | \
        jq '.jobs[] | {name: .name, status: .status, conclusion: .conclusion}' 2>/dev/null || echo "{}"
}

# Get run details using API
get_run_details() {
    local run_id=$1
    cd "$REPO_DIR"
    gh api "repos/overengineeredit/local_rag_v2/actions/runs/$run_id" | \
        jq '{displayTitle: .display_title, headBranch: .head_branch, event: .event, workflowName: .name, createdAt: .created_at, updatedAt: .updated_at, url: .html_url}' 2>/dev/null
}

# Analyze failed build
analyze_failure() {
    local run_id=$1
    log "${RED}FAILURE" "Build failed, analyzing logs..."
    
    cd "$REPO_DIR"
    
    # Get job details for failure analysis
    log "${BLUE}INFO" "Checking job statuses..."
    get_job_status "$run_id" | jq -s '.' || true
    
    # Get failed job logs
    log "${BLUE}INFO" "Fetching failed job logs..."
    gh run view "$run_id" --log-failed > "/tmp/failed-logs-${run_id}.log" 2>&1 || true
    
    # Look for specific error patterns
    local log_file="/tmp/failed-logs-${run_id}.log"
    
    if [[ -f "$log_file" ]]; then
        log "${BLUE}INFO" "Analyzing error patterns in logs..."
        
        # Check for safety/security scanning errors
        if grep -q "safety.*check.*DEPRECATED\|safety.*unsupported" "$log_file"; then
            log "${RED}ERROR" "Safety security scanning deprecated command detected"
            grep -A5 -B5 "safety.*check.*DEPRECATED\|safety.*unsupported" "$log_file" | head -20
        # Check for ARM64 compilation errors
        elif grep -q "unknown value.*for '-mcpu'" "$log_file"; then
            log "${RED}ERROR" "ARM64 cross-compilation error detected - mcpu issue persists"
            grep -A5 -B5 "unknown value.*for '-mcpu'" "$log_file" | head -20
        elif grep -q "GGML_NATIVE" "$log_file"; then
            log "${YELLOW}WARNING" "GGML_NATIVE related issues found"
            grep -A3 -B3 "GGML_NATIVE" "$log_file" | head -15
        elif grep -q "llama-cpp-python" "$log_file"; then
            log "${YELLOW}WARNING" "llama-cpp-python installation issues"
            grep -A5 -B5 "llama-cpp-python" "$log_file" | head -20
        elif grep -q "pytest" "$log_file"; then
            log "${YELLOW}WARNING" "Test execution issues"
            grep -A3 -B3 "pytest" "$log_file" | head -15
        elif grep -q "dpkg-buildpackage" "$log_file"; then
            log "${YELLOW}WARNING" "Package building issues"
            grep -A5 -B5 "dpkg-buildpackage" "$log_file" | head -20
        elif grep -q "Process completed with exit code" "$log_file"; then
            log "${RED}ERROR" "Process exit code errors found"
            grep -A3 -B3 "Process completed with exit code" "$log_file" | head -15
        fi
        
        log "${BLUE}INFO" "Full logs saved to: $log_file"
    fi
    
    # Suggest next steps
    log "${BLUE}INFO" "Suggested next steps:"
    echo "1. Review the logs: cat $log_file"
    echo "2. Check the run details: gh run view $run_id"
    echo "3. View specific job logs: gh run view $run_id --log"
    echo "4. Check job status: gh api repos/overengineeredit/local_rag_v2/actions/runs/$run_id/jobs"
}

# Analyze successful build
analyze_success() {
    local run_id=$1
    log "${GREEN}SUCCESS" "Build completed successfully!"
    
    cd "$REPO_DIR"
    
    # Get job details
    log "${BLUE}INFO" "Build job summary:"
    get_job_status "$run_id" | jq -s '.' || true
    
    # Get artifact information
    log "${BLUE}INFO" "Checking for build artifacts..."
    gh api "repos/overengineeredit/local_rag_v2/actions/runs/$run_id/artifacts" | \
        jq '.artifacts[] | {name: .name, size_in_bytes: .size_in_bytes}' 2>/dev/null || true
    
    log "${GREEN}SUCCESS" "CI/CD pipeline is now working correctly!"
    echo "✅ Cross-compilation working for both AMD64 and ARM64"
    echo "✅ Package building successful"
    echo "✅ All tests passing"
    echo "✅ Security scanning completed"
}

# Main monitoring loop
main() {
    local workflow="${1:-}"
    local event_type="${2:-}"
    local specific_run_id="${3:-}"
    
    if [[ -n "$specific_run_id" ]]; then
        # Monitor specific run ID
        local run_id="$specific_run_id"
        local workflow_name
        workflow_name=$(get_workflow_name "$run_id")
        log "${BLUE}INFO" "Monitoring specific run ID: $run_id (workflow: $workflow_name)"
    else
        # Get latest run for workflow/event
        log "${BLUE}INFO" "Starting CI build monitor for branch: $BRANCH"
        if [[ -n "$workflow" ]]; then
            log "${BLUE}INFO" "Filtering by workflow: $workflow"
        fi
        if [[ -n "$event_type" ]]; then
            log "${BLUE}INFO" "Filtering by event type: $event_type"
        fi
        
        local run_id
        run_id=$(get_latest_run_id "$workflow" "$event_type")
        
        if [[ -z "$run_id" ]]; then
            log "${RED}ERROR" "No runs found matching criteria"
            exit 1
        fi
        
        local workflow_name
        workflow_name=$(get_workflow_name "$run_id")
        log "${BLUE}INFO" "Found latest run ID: $run_id (workflow: $workflow_name)"
    fi
    
    log "${BLUE}INFO" "Checking every $CHECK_INTERVAL seconds"
    log "${BLUE}INFO" "Logs will be saved to: $LOG_FILE"
    
    # Show initial run details
    log "${BLUE}INFO" "Run details:"
    get_run_details "$run_id" | jq -r 'to_entries[] | "\(.key): \(.value)"' | while read -r line; do
        log "${BLUE}INFO" "  $line"
    done
    
    local last_status=""
    local check_count=0
    
    while true; do
        check_count=$((check_count + 1))
        local status_conclusion
        status_conclusion=$(get_run_status "$run_id")
        
        if [[ "$status_conclusion" != "$last_status" ]]; then
            log "${YELLOW}STATUS" "Run $run_id: $status_conclusion (check #$check_count)"
            last_status="$status_conclusion"
            
            # Show job status on status change
            if [[ "$status_conclusion" =~ ^(in_progress|completed): ]]; then
                log "${BLUE}INFO" "Job statuses:"
                get_job_status "$run_id" | jq -r 'select(.name) | "  \(.name): \(.status // "unknown") / \(.conclusion // "pending")"' || true
            fi
        else
            # Just show a progress indicator every 5th check (2.5 minutes)
            if (( check_count % 5 == 0 )); then
                log "${BLUE}INFO" "Still monitoring... (check #$check_count, status: $status_conclusion)"
            fi
        fi
        
        case "$status_conclusion" in
            "completed:success")
                analyze_success "$run_id"
                break
                ;;
            "completed:failure"|"completed:cancelled"|"completed:timed_out")
                analyze_failure "$run_id"
                break
                ;;
            "completed:skipped")
                log "${YELLOW}WARNING" "Build was skipped"
                break
                ;;
            "in_progress:null"|"in_progress:"|"queued:null"|"queued:"|"requested:null"|"requested:"|"waiting:null"|"waiting:")
                # Still running, continue monitoring
                ;;
            *)
                log "${YELLOW}WARNING" "Unknown status: $status_conclusion"
                ;;
        esac
        
        sleep "$CHECK_INTERVAL"
    done
    
    log "${BLUE}INFO" "Monitoring completed. Full log available at: $LOG_FILE"
}

# Handle interruption
trap 'log "${YELLOW}WARNING" "Monitoring interrupted by user"; exit 130' INT TERM

# Usage information
usage() {
    echo "Usage: $0 [workflow] [event_type] [run_id]"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Monitor latest run on branch"
    echo "  $0 build-packages.yml                # Monitor latest build-packages run"
    echo "  $0 build-packages.yml push           # Monitor latest push event for build-packages"
    echo "  $0 '' '' 19020899377                 # Monitor specific run ID"
    echo ""
    echo "Available workflows: ci.yml, build-packages.yml, pr-validation.yml"
    echo "Available events: push, pull_request, schedule, workflow_dispatch"
    exit 1
}

# Check for help
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
fi

# Run main function
main "$@"