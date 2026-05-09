#!/usr/bin/env python3
"""
Proper MCP Protocol Test
Tests MCP servers by actually communicating via stdio (the MCP protocol)
"""

import asyncio
import json
import subprocess
import sys
import os

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

class MCPClient:
    """Simple MCP client for testing"""
    
    def __init__(self, server_path):
        self.server_path = server_path
        self.process = None
        
    async def start(self):
        """Start the MCP server process"""
        python_path = sys.executable
        self.process = await asyncio.create_subprocess_exec(
            python_path, self.server_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, 'FHIR_BASE_URL': 'http://localhost:8080/fhir'}
        )
        
    async def send_request(self, method, params=None):
        """Send a JSON-RPC request to the server"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await asyncio.wait_for(
            self.process.stdout.readline(),
            timeout=5.0
        )
        
        if response_line:
            return json.loads(response_line.decode())
        return None
        
    async def stop(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            await self.process.wait()

async def test_payer_rules_mcp():
    """Test Payer Rules MCP Server via MCP protocol"""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Testing Payer Rules MCP via MCP Protocol{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")
    
    server_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'mcp-servers',
        'payer-rules-mcp',
        'server.py'
    )
    
    client = MCPClient(server_path)
    
    try:
        print(f"{YELLOW}Starting MCP server...{NC}")
        await client.start()
        await asyncio.sleep(1)  # Give server time to start
        print(f"{GREEN}✓ Server started{NC}\n")
        
        # Test 1: Initialize
        print(f"{YELLOW}Test 1: Initialize connection{NC}")
        response = await client.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })
        
        if response and "result" in response:
            print(f"  Server name: {response['result'].get('serverInfo', {}).get('name', 'unknown')}")
            print(f"  {GREEN}✓ PASS{NC}\n")
        else:
            print(f"  {RED}✗ FAIL: {response}{NC}\n")
            return False
        
        # Test 2: List tools
        print(f"{YELLOW}Test 2: List available tools{NC}")
        response = await client.send_request("tools/list")
        
        if response and "result" in response:
            tools = response['result'].get('tools', [])
            print(f"  Tools found: {len(tools)}")
            for tool in tools:
                print(f"    - {tool.get('name', 'unknown')}")
            print(f"  {GREEN}✓ PASS{NC}\n")
        else:
            print(f"  {RED}✗ FAIL: {response}{NC}\n")
            return False
        
        # Test 3: Call list_payers tool
        print(f"{YELLOW}Test 3: Call list_payers tool{NC}")
        response = await client.send_request("tools/call", {
            "name": "list_payers",
            "arguments": {}
        })
        
        if response and "result" in response:
            content = response['result'].get('content', [])
            if content:
                data = json.loads(content[0].get('text', '{}'))
                print(f"  Payers found: {data.get('count', 0)}")
                for payer in data.get('payers', []):
                    print(f"    - {payer}")
                print(f"  {GREEN}✓ PASS{NC}\n")
            else:
                print(f"  {RED}✗ FAIL: No content in response{NC}\n")
                return False
        else:
            print(f"  {RED}✗ FAIL: {response}{NC}\n")
            return False
        
        # Test 4: Call check_auth_requirements tool
        print(f"{YELLOW}Test 4: Call check_auth_requirements tool{NC}")
        response = await client.send_request("tools/call", {
            "name": "check_auth_requirements",
            "arguments": {
                "payer": "Blue Cross Blue Shield",
                "procedure_or_medication": "MRI"
            }
        })
        
        if response and "result" in response:
            content = response['result'].get('content', [])
            if content:
                data = json.loads(content[0].get('text', '{}'))
                print(f"  Payer: {data.get('payer', 'unknown')}")
                print(f"  Procedure: {data.get('procedure_or_medication', 'unknown')}")
                print(f"  Requires auth: {data.get('requires_prior_authorization', 'unknown')}")
                print(f"  Turnaround: {data.get('turnaround_time_hours', 0)} hours")
                print(f"  {GREEN}✓ PASS{NC}\n")
            else:
                print(f"  {RED}✗ FAIL: No content in response{NC}\n")
                return False
        else:
            print(f"  {RED}✗ FAIL: {response}{NC}\n")
            return False
        
        return True
        
    except asyncio.TimeoutError:
        print(f"  {RED}✗ FAIL: Timeout waiting for server response{NC}\n")
        return False
    except Exception as e:
        print(f"  {RED}✗ FAIL: {str(e)}{NC}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.stop()

async def test_patient_records_mcp():
    """Test Patient Records MCP Server via MCP protocol"""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Testing Patient Records MCP via MCP Protocol{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")
    
    server_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'mcp-servers',
        'patient-records-mcp',
        'server.py'
    )
    
    client = MCPClient(server_path)
    
    try:
        print(f"{YELLOW}Starting MCP server...{NC}")
        await client.start()
        await asyncio.sleep(1)
        print(f"{GREEN}✓ Server started{NC}\n")
        
        # Test 1: Initialize
        print(f"{YELLOW}Test 1: Initialize connection{NC}")
        response = await client.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })
        
        if response and "result" in response:
            print(f"  Server name: {response['result'].get('serverInfo', {}).get('name', 'unknown')}")
            print(f"  {GREEN}✓ PASS{NC}\n")
        else:
            print(f"  {RED}✗ FAIL: {response}{NC}\n")
            return False
        
        # Test 2: List tools
        print(f"{YELLOW}Test 2: List available tools{NC}")
        response = await client.send_request("tools/list")
        
        if response and "result" in response:
            tools = response['result'].get('tools', [])
            print(f"  Tools found: {len(tools)}")
            for tool in tools[:3]:  # Show first 3
                print(f"    - {tool.get('name', 'unknown')}")
            if len(tools) > 3:
                print(f"    ... and {len(tools) - 3} more")
            print(f"  {GREEN}✓ PASS{NC}\n")
        else:
            print(f"  {RED}✗ FAIL: {response}{NC}\n")
            return False
        
        # Test 3: Call get_patient_demographics tool
        print(f"{YELLOW}Test 3: Call get_patient_demographics tool{NC}")
        response = await client.send_request("tools/call", {
            "name": "get_patient_demographics",
            "arguments": {
                "patient_id": "64513"
            }
        })
        
        if response and "result" in response:
            content = response['result'].get('content', [])
            if content:
                data = json.loads(content[0].get('text', '{}'))
                print(f"  Patient ID: {data.get('id', 'unknown')}")
                name = data.get('name', {})
                print(f"  Family name: {name.get('family', 'unknown')}")
                print(f"  Gender: {data.get('gender', 'unknown')}")
                print(f"  {GREEN}✓ PASS{NC}\n")
            else:
                print(f"  {RED}✗ FAIL: No content in response{NC}\n")
                return False
        else:
            print(f"  {RED}✗ FAIL: {response}{NC}\n")
            return False
        
        # Test 4: Call get_prior_auth_summary tool
        print(f"{YELLOW}Test 4: Call get_prior_auth_summary tool{NC}")
        response = await client.send_request("tools/call", {
            "name": "get_prior_auth_summary",
            "arguments": {
                "patient_id": "64513"
            }
        })
        
        if response and "result" in response:
            content = response['result'].get('content', [])
            if content:
                data = json.loads(content[0].get('text', '{}'))
                patient = data.get('patient', {})
                print(f"  Patient ID: {patient.get('id', 'unknown')}")
                print(f"  Active conditions: {len(data.get('active_conditions', []))}")
                print(f"  Current medications: {len(data.get('current_medications', []))}")
                print(f"  Recent procedures: {len(data.get('recent_procedures', []))}")
                print(f"  Recent labs: {len(data.get('recent_labs', []))}")
                print(f"  {GREEN}✓ PASS{NC}\n")
            else:
                print(f"  {RED}✗ FAIL: No content in response{NC}\n")
                return False
        else:
            print(f"  {RED}✗ FAIL: {response}{NC}\n")
            return False
        
        return True
        
    except asyncio.TimeoutError:
        print(f"  {RED}✗ FAIL: Timeout waiting for server response{NC}\n")
        return False
    except Exception as e:
        print(f"  {RED}✗ FAIL: {str(e)}{NC}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.stop()

async def main():
    """Run all MCP protocol tests"""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}MCP Protocol Tests{NC}")
    print(f"{BLUE}Testing servers via actual MCP stdio communication{NC}")
    print(f"{BLUE}{'='*60}{NC}")
    
    # Test Payer Rules MCP
    payer_pass = await test_payer_rules_mcp()
    
    # Test Patient Records MCP
    patient_pass = await test_patient_records_mcp()
    
    # Summary
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}Test Summary{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")
    
    if payer_pass:
        print(f"{GREEN}✓ Payer Rules MCP: All protocol tests passed{NC}")
    else:
        print(f"{RED}✗ Payer Rules MCP: Some tests failed{NC}")
    
    if patient_pass:
        print(f"{GREEN}✓ Patient Records MCP: All protocol tests passed{NC}")
    else:
        print(f"{RED}✗ Patient Records MCP: Some tests failed{NC}")
    
    print()
    
    if payer_pass and patient_pass:
        print(f"{GREEN}✓ All MCP protocol tests passed!{NC}")
        print(f"\n{BLUE}Both servers are communicating correctly via MCP protocol.{NC}")
        print(f"{BLUE}They are ready for use in Prompt Opinion.{NC}\n")
        return 0
    else:
        print(f"{RED}✗ Some tests failed. Please check the errors above.{NC}\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
