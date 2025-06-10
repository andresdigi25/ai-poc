#!/bin/bash

# CoT Mapping System - Backup Script
echo "🔄 Starting backup process..."

# Configuration
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_FILE="cot_mappings.db"
BACKUP_FILE="${BACKUP_DIR}/cot_mappings_backup_${TIMESTAMP}.db"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    echo "❌ Database file not found: $DB_FILE"
    exit 1
fi

# Create backup
echo "📁 Creating backup: $BACKUP_FILE"
cp "$DB_FILE" "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully: $BACKUP_FILE"
    
    # Get backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "📦 Backup size: $BACKUP_SIZE"
    
    # Compress backup (optional)
    echo "🗜️ Compressing backup..."
    gzip "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Backup compressed: ${BACKUP_FILE}.gz"
        COMPRESSED_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
        echo "📦 Compressed size: $COMPRESSED_SIZE"
    fi
    
    # Clean old backups (keep last 10)
    echo "🧹 Cleaning old backups..."
    ls -t ${BACKUP_DIR}/cot_mappings_backup_*.gz 2>/dev/null | tail -n +11 | xargs rm -f
    
    REMAINING_BACKUPS=$(ls ${BACKUP_DIR}/cot_mappings_backup_*.gz 2>/dev/null | wc -l)
    echo "📋 Remaining backups: $REMAINING_BACKUPS"
    
else
    echo "❌ Backup failed"
    exit 1
fi

echo "🎉 Backup process completed successfully"