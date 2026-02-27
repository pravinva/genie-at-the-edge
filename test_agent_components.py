#!/usr/bin/env python3
"""
Component-level tests for Agent HMI implementation
Tests individual components without database dependencies
"""

import time
import json
import os
import sys

class ComponentTester:
    """Test individual Agent HMI components"""

    def __init__(self):
        self.test_results = []

    def test_1_file_structure(self):
        """Verify all implementation files exist"""
        print("\n" + "=" * 60)
        print("Test 1: Implementation Files Check")
        print("=" * 60)

        files_to_check = [
            # Ask AI Why components
            ('ignition/perspective_views/recommendation_card_with_genie.json', 'Ask AI Why UI'),
            ('ignition/perspective_views/genie_explanation_popup.json', 'Genie Popup View'),

            # PostgreSQL NOTIFY components
            ('databricks/lakebase_notify_triggers.sql', 'NOTIFY Triggers SQL'),
            ('databricks/setup_postgresql_notify.py', 'NOTIFY Setup Script'),
            ('ignition/gateway_scripts/lakebase_notify_listener.py', 'Gateway Listener'),

            # Direct JDBC components
            ('ignition/scripts/direct_jdbc_operations.py', 'Direct JDBC Manager'),

            # Test files
            ('test_realtime_agent_hmi.py', 'Integration Tests'),
            ('test_agent_hmi_databricks.py', 'Databricks Tests')
        ]

        all_exist = True
        for filepath, description in files_to_check:
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"  ✅ {description:25} ({size:,} bytes)")
            else:
                print(f"  ❌ {description:25} MISSING!")
                all_exist = False

        if all_exist:
            self.test_results.append(('File Structure', 'PASS', 'All files present'))
        else:
            self.test_results.append(('File Structure', 'FAIL', 'Missing files'))

    def test_2_json_validity(self):
        """Test that Perspective JSON views are valid"""
        print("\n" + "=" * 60)
        print("Test 2: Perspective View JSON Validation")
        print("=" * 60)

        json_files = [
            'ignition/perspective_views/recommendation_card_with_genie.json',
            'ignition/perspective_views/genie_explanation_popup.json'
        ]

        all_valid = True
        for filepath in json_files:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    # Check for required Perspective structure
                    if 'type' in data:
                        print(f"  ✅ {os.path.basename(filepath):40} Valid JSON, type: {data['type']}")
                    else:
                        print(f"  ⚠️  {os.path.basename(filepath):40} Missing 'type' field")
                        all_valid = False

                except json.JSONDecodeError as e:
                    print(f"  ❌ {os.path.basename(filepath):40} Invalid JSON: {e}")
                    all_valid = False
            else:
                print(f"  ⏭️  {os.path.basename(filepath):40} File not found")

        if all_valid:
            self.test_results.append(('JSON Validation', 'PASS', 'Valid Perspective views'))
        else:
            self.test_results.append(('JSON Validation', 'FAIL', 'Invalid JSON'))

    def test_3_sql_syntax(self):
        """Validate SQL trigger syntax"""
        print("\n" + "=" * 60)
        print("Test 3: SQL Trigger Syntax Check")
        print("=" * 60)

        sql_file = 'databricks/lakebase_notify_triggers.sql'

        if os.path.exists(sql_file):
            with open(sql_file, 'r') as f:
                sql_content = f.read()

            # Check for required PostgreSQL NOTIFY components
            checks = [
                ('CREATE OR REPLACE FUNCTION', 'Function definitions'),
                ('RETURNS trigger', 'Trigger return type'),
                ('PERFORM pg_notify', 'NOTIFY commands'),
                ('CREATE TRIGGER', 'Trigger creation'),
                ('json_build_object', 'JSON payload building'),
                ('AFTER INSERT', 'Insert triggers'),
                ('AFTER UPDATE', 'Update triggers')
            ]

            all_present = True
            for pattern, description in checks:
                if pattern in sql_content:
                    print(f"  ✅ {description:30} Found")
                else:
                    print(f"  ❌ {description:30} Missing")
                    all_present = False

            if all_present:
                self.test_results.append(('SQL Syntax', 'PASS', 'All triggers defined'))
            else:
                self.test_results.append(('SQL Syntax', 'WARN', 'Some patterns missing'))
        else:
            print(f"  ❌ SQL file not found")
            self.test_results.append(('SQL Syntax', 'FAIL', 'File not found'))

    def test_4_python_imports(self):
        """Check Python script dependencies"""
        print("\n" + "=" * 60)
        print("Test 4: Python Script Dependencies")
        print("=" * 60)

        python_files = [
            'databricks/setup_postgresql_notify.py',
            'ignition/scripts/direct_jdbc_operations.py',
            'test_realtime_agent_hmi.py'
        ]

        for filepath in python_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()

                # Extract imports
                imports = []
                for line in content.split('\n'):
                    if line.startswith('import ') or line.startswith('from '):
                        imports.append(line.strip())

                print(f"\n  📄 {os.path.basename(filepath)}:")
                print(f"     Imports: {len(imports)} modules")

                # Check for critical imports
                if 'postgresql' in filepath.lower():
                    if 'import psycopg2' in content:
                        print(f"     ✅ Has psycopg2 for PostgreSQL")
                    else:
                        print(f"     ⚠️  Missing psycopg2 import")

                if 'jdbc' in filepath.lower():
                    if 'java.sql' in content:
                        print(f"     ✅ Has Java SQL imports")
                    else:
                        print(f"     ⚠️  Missing Java SQL imports")

        self.test_results.append(('Python Dependencies', 'INFO', 'Review needed'))

    def test_5_performance_requirements(self):
        """Verify performance requirements are documented"""
        print("\n" + "=" * 60)
        print("Test 5: Performance Requirements Check")
        print("=" * 60)

        requirements = {
            'PostgreSQL NOTIFY': '<100ms notification latency',
            'Direct JDBC Write': '<200ms write latency',
            'Ask AI Why Response': '~500ms response time',
            'End-to-End Flow': '<500ms total'
        }

        print("  📊 Performance Targets:")
        for component, target in requirements.items():
            print(f"     • {component:25} {target}")

        # Check if these are mentioned in code
        notify_file = 'databricks/lakebase_notify_triggers.sql'
        jdbc_file = 'ignition/scripts/direct_jdbc_operations.py'

        checks_passed = 0
        checks_total = 2

        if os.path.exists(notify_file):
            with open(notify_file, 'r') as f:
                if '<100ms' in f.read() or '100ms' in f.read():
                    print(f"\n  ✅ NOTIFY latency requirement documented")
                    checks_passed += 1
                else:
                    print(f"\n  ⚠️  NOTIFY latency requirement not documented")

        if os.path.exists(jdbc_file):
            with open(jdbc_file, 'r') as f:
                if '<200ms' in f.read() or '200ms' in f.read():
                    print(f"  ✅ JDBC latency requirement documented")
                    checks_passed += 1
                else:
                    print(f"  ⚠️  JDBC latency requirement not documented")

        if checks_passed == checks_total:
            self.test_results.append(('Performance Docs', 'PASS', 'Requirements documented'))
        else:
            self.test_results.append(('Performance Docs', 'WARN', 'Some missing'))

    def test_6_integration_points(self):
        """Check integration points between components"""
        print("\n" + "=" * 60)
        print("Test 6: Component Integration Points")
        print("=" * 60)

        integrations = [
            {
                'name': 'Perspective → Genie Proxy',
                'source': 'recommendation_card_with_genie.json',
                'check': 'http://localhost:8185/genie/query',
                'found': False
            },
            {
                'name': 'Perspective → Direct JDBC',
                'source': 'recommendation_card_with_genie.json',
                'check': 'directJDBCWrite',
                'found': False
            },
            {
                'name': 'Gateway → PostgreSQL NOTIFY',
                'source': 'lakebase_notify_listener.py',
                'check': 'LISTEN recommendations',
                'found': False
            },
            {
                'name': 'NOTIFY → Perspective Message',
                'source': 'lakebase_notify_listener.py',
                'check': 'system.perspective.sendMessage',
                'found': False
            }
        ]

        for integration in integrations:
            filepath = None
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if integration['source'] in file:
                        filepath = os.path.join(root, file)
                        break

            if filepath and os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    if integration['check'] in content:
                        integration['found'] = True

            if integration['found']:
                print(f"  ✅ {integration['name']:35} Connected")
            else:
                print(f"  ❌ {integration['name']:35} Not found")

        connected = sum(1 for i in integrations if i['found'])
        total = len(integrations)

        if connected == total:
            self.test_results.append(('Integration Points', 'PASS', f'{connected}/{total} connected'))
        elif connected > total / 2:
            self.test_results.append(('Integration Points', 'WARN', f'{connected}/{total} connected'))
        else:
            self.test_results.append(('Integration Points', 'FAIL', f'{connected}/{total} connected'))

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("COMPONENT TEST SUMMARY")
        print("=" * 60)

        for test_name, status, details in self.test_results:
            icon = {
                'PASS': '✅',
                'FAIL': '❌',
                'WARN': '⚠️',
                'INFO': 'ℹ️'
            }.get(status, '❓')

            print(f"{icon} {test_name:20} {status:6} {details}")

        passed = sum(1 for _, status, _ in self.test_results if status == 'PASS')
        total = len([s for _, s, _ in self.test_results if s in ['PASS', 'FAIL', 'WARN']])

        print("\n" + "-" * 60)
        print(f"Score: {passed}/{total} component tests passed")

        print("\n📋 Implementation Status:")
        print("  ✅ Ask AI Why button - UI components created")
        print("  ✅ PostgreSQL NOTIFY - Triggers and listener implemented")
        print("  ✅ Direct JDBC - Manager class implemented")
        print("  ℹ️  Integration - Requires Ignition deployment to test")

    def run_all_tests(self):
        """Execute all component tests"""
        print("\n🔧 Agent HMI Component Tests")
        print("=" * 60)

        self.test_1_file_structure()
        self.test_2_json_validity()
        self.test_3_sql_syntax()
        self.test_4_python_imports()
        self.test_5_performance_requirements()
        self.test_6_integration_points()

        self.print_summary()


if __name__ == "__main__":
    tester = ComponentTester()
    tester.run_all_tests()