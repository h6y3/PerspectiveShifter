#!/usr/bin/env python3
"""
Performance testing for sharing functionality
PERMANENT SCRIPT - Should be committed to repo

This script tests performance characteristics of sharing routes,
including response times, memory usage, and concurrency handling.

Usage:
    python scripts/performance_test_sharing.py
    python scripts/performance_test_sharing.py --url https://your-app.vercel.app --concurrent 10
"""

import requests
import time
import statistics
import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

DEFAULT_URL = "https://theperspectiveshift.vercel.app"
DEFAULT_CONCURRENT = 5
DEFAULT_ITERATIONS = 20

class PerformanceTester:
    def __init__(self, base_url=DEFAULT_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PerspectiveShifter-Performance/1.0'
        })
        self.results = []
        
    def generate_test_quote(self):
        """Generate a quote for testing"""
        try:
            data = {'user_input': 'performance testing scenario'}
            response = self.session.post(f"{self.base_url}/shift", data=data, timeout=30)
            if response.status_code == 200:
                import re
                html = response.text
                match = re.search(r'data-quote-id="([^"]+)"', html)
                if match:
                    return match.group(1)
            return None
        except Exception:
            return None
    
    def test_endpoint_performance(self, endpoint, method='GET', data=None, iterations=10):
        """Test performance of a specific endpoint"""
        print(f"🚀 Testing {method} {endpoint} ({iterations} iterations)")
        
        response_times = []
        errors = 0
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                if method == 'GET':
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
                elif method == 'POST':
                    response = self.session.post(f"{self.base_url}{endpoint}", 
                                               json=data if data else {}, timeout=30)
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code not in [200, 302]:
                    errors += 1
                    
            except Exception as e:
                errors += 1
                print(f"  Error in iteration {i+1}: {e}")
        
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            median_time = statistics.median(response_times)
            
            print(f"  📊 Results:")
            print(f"    Average: {avg_time:.3f}s")
            print(f"    Median:  {median_time:.3f}s")
            print(f"    Min:     {min_time:.3f}s")
            print(f"    Max:     {max_time:.3f}s")
            print(f"    Errors:  {errors}/{iterations}")
            
            return {
                'endpoint': endpoint,
                'method': method,
                'avg_time': avg_time,
                'median_time': median_time,
                'min_time': min_time,
                'max_time': max_time,
                'errors': errors,
                'total_requests': iterations,
                'error_rate': errors / iterations
            }
        else:
            print(f"  ❌ All requests failed")
            return None
    
    def test_concurrent_requests(self, endpoint, concurrent_users=5, requests_per_user=4):
        """Test concurrent access to an endpoint"""
        print(f"🔄 Testing concurrent access: {concurrent_users} users, {requests_per_user} requests each")
        
        def make_request(user_id):
            """Make a request as a specific user"""
            user_times = []
            user_errors = 0
            
            for req_num in range(requests_per_user):
                try:
                    start_time = time.time()
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
                    response_time = time.time() - start_time
                    user_times.append(response_time)
                    
                    if response.status_code not in [200, 302]:
                        user_errors += 1
                        
                except Exception:
                    user_errors += 1
            
            return {
                'user_id': user_id,
                'times': user_times,
                'errors': user_errors
            }
        
        # Execute concurrent requests
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_request, i) for i in range(concurrent_users)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        all_times = []
        total_errors = 0
        total_requests = 0
        
        for result in results:
            all_times.extend(result['times'])
            total_errors += result['errors']
            total_requests += len(result['times']) + result['errors']
        
        if all_times:
            avg_time = statistics.mean(all_times)
            throughput = total_requests / total_time
            
            print(f"  📊 Concurrent Results:")
            print(f"    Total time:    {total_time:.3f}s")
            print(f"    Avg response:  {avg_time:.3f}s")
            print(f"    Throughput:    {throughput:.1f} req/s")
            print(f"    Error rate:    {total_errors}/{total_requests} ({100*total_errors/total_requests:.1f}%)")
            
            return {
                'concurrent_users': concurrent_users,
                'total_time': total_time,
                'avg_response_time': avg_time,
                'throughput': throughput,
                'error_rate': total_errors / total_requests
            }
        
        return None
    
    def test_image_generation_performance(self, quote_id, iterations=5):
        """Test image generation performance specifically"""
        print(f"🖼️  Testing image generation performance ({iterations} iterations)")
        
        designs = [1, 2, 3]
        results = {}
        
        for design in designs:
            endpoint = f"/image/{quote_id}?design={design}"
            result = self.test_endpoint_performance(endpoint, iterations=iterations)
            if result:
                results[f"design_{design}"] = result
        
        return results
    
    def test_vercel_limits(self, quote_id):
        """Test against Vercel's specific limits"""
        print("⚡ Testing Vercel serverless function limits...")
        
        # Test function duration (should be well under 60s)
        print("  Testing function duration...")
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/image/{quote_id}?design=3", timeout=60)
            duration = time.time() - start_time
            
            if duration < 10:
                print(f"  ✅ Fast generation: {duration:.2f}s (well under 60s limit)")
            elif duration < 30:
                print(f"  ⚠️  Moderate generation: {duration:.2f}s (acceptable)")
            else:
                print(f"  ❌ Slow generation: {duration:.2f}s (concerning)")
                
        except Exception as e:
            print(f"  ❌ Function duration test failed: {e}")
        
        # Test memory efficiency (check response sizes)
        print("  Testing response sizes...")
        endpoints = [
            f"/share/{quote_id}",
            f"/image/{quote_id}",
            "/share-stats"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    size_kb = len(response.content) / 1024
                    content_type = response.headers.get('Content-Type', '')
                    print(f"    {endpoint}: {size_kb:.1f} KB ({content_type})")
            except Exception as e:
                print(f"    {endpoint}: Error - {e}")
    
    def run_performance_tests(self, concurrent_users=5, iterations=10):
        """Run comprehensive performance tests"""
        print(f"⚡ Performance Testing for {self.base_url}")
        print("=" * 60)
        
        # Generate test quote
        print("🔍 Setting up test data...")
        quote_id = self.generate_test_quote()
        
        if not quote_id:
            print("❌ Cannot generate test quote - using placeholder")
            quote_id = "1_0"  # Fallback
        else:
            print(f"✅ Using quote ID: {quote_id}")
        
        # Test individual endpoints
        print(f"\n📊 INDIVIDUAL ENDPOINT PERFORMANCE")
        print("-" * 40)
        
        endpoints_to_test = [
            ("/health", "GET"),
            (f"/share/{quote_id}", "GET"),
            (f"/image/{quote_id}", "GET"),
            ("/share-stats", "GET"),
            (f"/track-share/{quote_id}", "POST", {"platform": "x"})
        ]
        
        endpoint_results = []
        for endpoint_info in endpoints_to_test:
            endpoint = endpoint_info[0]
            method = endpoint_info[1]
            data = endpoint_info[2] if len(endpoint_info) > 2 else None
            
            result = self.test_endpoint_performance(endpoint, method, data, iterations)
            if result:
                endpoint_results.append(result)
        
        # Test concurrent access
        print(f"\n🔄 CONCURRENT ACCESS TESTING")
        print("-" * 40)
        
        concurrent_results = []
        
        # Test different concurrency levels
        for users in [2, 5, 10]:
            if users <= concurrent_users:
                result = self.test_concurrent_requests(f"/share/{quote_id}", users, 3)
                if result:
                    concurrent_results.append(result)
        
        # Test image generation performance
        print(f"\n🖼️  IMAGE GENERATION PERFORMANCE")
        print("-" * 40)
        
        image_results = self.test_image_generation_performance(quote_id, 3)
        
        # Test Vercel-specific limits
        print(f"\n⚡ VERCEL LIMITS TESTING")
        print("-" * 40)
        
        self.test_vercel_limits(quote_id)
        
        # Performance summary
        print(f"\n📈 PERFORMANCE SUMMARY")
        print("=" * 60)
        
        # Find slowest endpoints
        if endpoint_results:
            slowest = max(endpoint_results, key=lambda x: x['avg_time'])
            fastest = min(endpoint_results, key=lambda x: x['avg_time'])
            
            print(f"Fastest endpoint: {fastest['endpoint']} ({fastest['avg_time']:.3f}s avg)")
            print(f"Slowest endpoint: {slowest['endpoint']} ({slowest['avg_time']:.3f}s avg)")
            
            # Check for performance issues
            slow_endpoints = [r for r in endpoint_results if r['avg_time'] > 5.0]
            if slow_endpoints:
                print(f"\n⚠️  Slow endpoints (>5s):")
                for ep in slow_endpoints:
                    print(f"  - {ep['endpoint']}: {ep['avg_time']:.3f}s")
            
            # Check error rates
            high_error_endpoints = [r for r in endpoint_results if r['error_rate'] > 0.1]
            if high_error_endpoints:
                print(f"\n❌ High error rate endpoints (>10%):")
                for ep in high_error_endpoints:
                    print(f"  - {ep['endpoint']}: {ep['error_rate']:.1%}")
        
        # Concurrency summary
        if concurrent_results:
            best_throughput = max(concurrent_results, key=lambda x: x['throughput'])
            print(f"\nBest throughput: {best_throughput['throughput']:.1f} req/s with {best_throughput['concurrent_users']} users")
        
        print(f"\n✅ Performance testing completed!")
        
        # Return summary for programmatic use
        return {
            'endpoint_results': endpoint_results,
            'concurrent_results': concurrent_results,
            'image_results': image_results
        }

def main():
    parser = argparse.ArgumentParser(description='Performance test sharing functionality')
    parser.add_argument('--url', default=DEFAULT_URL,
                       help=f'Base URL to test (default: {DEFAULT_URL})')
    parser.add_argument('--concurrent', type=int, default=DEFAULT_CONCURRENT,
                       help=f'Max concurrent users to test (default: {DEFAULT_CONCURRENT})')
    parser.add_argument('--iterations', type=int, default=DEFAULT_ITERATIONS,
                       help=f'Iterations per test (default: {DEFAULT_ITERATIONS})')
    
    args = parser.parse_args()
    
    tester = PerformanceTester(args.url)
    results = tester.run_performance_tests(args.concurrent, args.iterations)
    
    # Exit with error code if there were significant performance issues
    if results['endpoint_results']:
        avg_times = [r['avg_time'] for r in results['endpoint_results']]
        error_rates = [r['error_rate'] for r in results['endpoint_results']]
        
        if max(avg_times) > 10.0 or max(error_rates) > 0.2:
            sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()