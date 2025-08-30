#!/usr/bin/env python3
"""
Session Cleanup Helper Script

This script provides easy commands to manage and cleanup sessions.
"""

import requests
import argparse
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/sessions"

def list_sessions(show_inactive=False):
    """List all sessions with their status"""
    try:
        response = requests.get(f"{API_BASE}/list", params={'show_inactive': show_inactive})
        if response.status_code == 200:
            data = response.json()
            
            print(f"=== Session Status ===")
            print(f"Total sessions: {data['total']}")
            print(f"Active sessions: {data['activeCount']} (with meaningful data)")
            print(f"Inactive sessions: {data['inactiveCount']} (empty/minimal data)")
            
            if data['sessions']:
                print(f"\n=== Session Details ===")
                for session in data['sessions']:
                    status = "🟢 Active" if session['hasActivity'] else "🔴 Inactive"
                    print(f"{session['sessionId'][:20]}... | {status} | {session['ageString']} | "
                          f"{session['chatMessages']} msgs | {session['studiesFound']} studies")
            
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error connecting to server: {e}")

def cleanup_sessions(inactive_only=True, older_than_hours=0, force_all=False, dry_run=False):
    """Cleanup sessions based on criteria"""
    try:
        if dry_run:
            print("=== DRY RUN - No actual cleanup will be performed ===")
            
        params = {
            'inactive_only': inactive_only,
            'older_than_hours': older_than_hours,
            'force_all': force_all
        }
        
        if dry_run:
            print(f"Would cleanup with parameters: {params}")
            return
            
        response = requests.post(f"{API_BASE}/cleanup", params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print(f"✅ Cleanup Successful!")
                print(f"Cleaned sessions: {data['cleanedSessions']}")
                print(f"Total resources removed: {data['totalResources']}")
                
                if data['sessions']:
                    print(f"\n=== Cleaned Sessions ===")
                    for session in data['sessions']:
                        activity = "(had activity)" if session['hadActivity'] else "(inactive)"
                        age = f"{session['age']:.1f}h old"
                        print(f"{session['sessionId'][:20]}... {activity} - {age} - {session['resourcesCleaned']} resources")
            else:
                print(f"❌ Cleanup Failed: {data.get('error')}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error connecting to server: {e}")

def delete_session(session_id):
    """Delete a specific session"""
    try:
        response = requests.delete(f"{API_BASE}/{session_id}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print(f"✅ Session {session_id} deleted successfully!")
                print(f"Cleaned resources: {data['cleanedResources']}")
            else:
                print(f"❌ Failed to delete session: {data.get('error')}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error connecting to server: {e}")

def main():
    parser = argparse.ArgumentParser(description="Clinical Trials Session Cleanup Helper")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List sessions')
    list_parser.add_argument('--all', action='store_true', help='Show inactive sessions too')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup sessions')
    cleanup_parser.add_argument('--all-sessions', action='store_true', help='Clean active sessions too')
    cleanup_parser.add_argument('--older-than', type=int, default=1, help='Clean sessions older than X hours')
    cleanup_parser.add_argument('--force-all', action='store_true', help='Clean ALL sessions regardless of age')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned without doing it')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete specific session')
    delete_parser.add_argument('session_id', help='Session ID to delete')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_sessions(show_inactive=args.all)
    elif args.command == 'cleanup':
        cleanup_sessions(
            inactive_only=not args.all_sessions,
            older_than_hours=args.older_than,
            force_all=args.force_all,
            dry_run=args.dry_run
        )
    elif args.command == 'delete':
        delete_session(args.session_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()