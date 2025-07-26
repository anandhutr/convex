#!/bin/bash

# Convex Studio Inventory - Deployment Script
# This script handles deployment and upgrades for different environments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
ACTION=${2:-deploy}

# Environment-specific settings
case $ENVIRONMENT in
    "development")
        COMPOSE_PROFILE=""
        FLASK_ENV="development"
        ;;
    "staging")
        COMPOSE_PROFILE="--profile staging"
        FLASK_ENV="staging"
        ;;
    "production")
        COMPOSE_PROFILE="--profile production"
        FLASK_ENV="production"
        ;;
    *)
        echo -e "${RED}Error: Invalid environment. Use: development, staging, or production${NC}"
        exit 1
        ;;
esac

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Python is installed (for local development)
    if ! command -v python &> /dev/null; then
        log_warning "Python is not installed. This is only needed for local development."
    fi
    
    log_success "Prerequisites check completed"
}

backup_database() {
    log_info "Creating database backup..."
    
    if [ -f "inventory.db" ]; then
        timestamp=$(date +"%Y%m%d_%H%M%S")
        backup_name="inventory_backup_${timestamp}.db"
        
        # Create backups directory if it doesn't exist
        mkdir -p backups
        
        cp inventory.db "backups/${backup_name}"
        log_success "Database backed up to: backups/${backup_name}"
    else
        log_warning "No existing database found to backup"
    fi
}

run_upgrade_script() {
    log_info "Running upgrade script..."
    
    if [ -f "upgrade_implementation.py" ]; then
        python upgrade_implementation.py
        log_success "Upgrade script completed"
    else
        log_warning "Upgrade script not found, skipping..."
    fi
}

deploy_application() {
    log_info "Deploying application to ${ENVIRONMENT} environment..."
    
    # Set environment variables
    export FLASK_ENV=$FLASK_ENV
    
    # Create necessary directories
    mkdir -p data uploads backups logs static templates
    
    # Build and start containers
    docker-compose $COMPOSE_PROFILE up -d --build
    
    log_success "Application deployed successfully"
}

stop_application() {
    log_info "Stopping application..."
    
    docker-compose $COMPOSE_PROFILE down
    
    log_success "Application stopped"
}

restart_application() {
    log_info "Restarting application..."
    
    docker-compose $COMPOSE_PROFILE restart
    
    log_success "Application restarted"
}

check_health() {
    log_info "Checking application health..."
    
    # Wait for application to start
    sleep 10
    
    # Check if application is responding
    if curl -f http://localhost:5000/health &> /dev/null; then
        log_success "Application is healthy"
        return 0
    else
        log_error "Application health check failed"
        return 1
    fi
}

show_logs() {
    log_info "Showing application logs..."
    
    docker-compose $COMPOSE_PROFILE logs -f inventory-app
}

cleanup() {
    log_info "Cleaning up old backups..."
    
    # Keep only the last 10 backups
    if [ -d "backups" ]; then
        cd backups
        ls -t inventory_backup_*.db | tail -n +11 | xargs -r rm
        cd ..
        log_success "Old backups cleaned up"
    fi
}

show_help() {
    echo "Convex Studio Inventory - Deployment Script"
    echo ""
    echo "Usage: $0 [environment] [action]"
    echo ""
    echo "Environments:"
    echo "  development  - Local development environment"
    echo "  staging      - Staging environment"
    echo "  production   - Production environment"
    echo ""
    echo "Actions:"
    echo "  deploy       - Deploy the application (default)"
    echo "  stop         - Stop the application"
    echo "  restart      - Restart the application"
    echo "  upgrade      - Run upgrade script and deploy"
    echo "  logs         - Show application logs"
    echo "  health       - Check application health"
    echo "  cleanup      - Clean up old backups"
    echo "  help         - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 development deploy"
    echo "  $0 production upgrade"
    echo "  $0 staging logs"
}

# Main script logic
case $ACTION in
    "deploy")
        check_prerequisites
        backup_database
        deploy_application
        check_health
        cleanup
        ;;
    "upgrade")
        check_prerequisites
        backup_database
        run_upgrade_script
        deploy_application
        check_health
        cleanup
        ;;
    "stop")
        stop_application
        ;;
    "restart")
        restart_application
        check_health
        ;;
    "logs")
        show_logs
        ;;
    "health")
        check_health
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        log_error "Invalid action: $ACTION"
        show_help
        exit 1
        ;;
esac

log_success "Deployment script completed successfully!" 