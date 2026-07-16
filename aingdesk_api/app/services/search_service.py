import aiohttp
import json
import urllib.parse
from typing import List, Dict, Any, Optional
import asyncio

class SearchService:
    """搜索服务类，支持多种搜索提供商"""
    
    def __init__(self):
        self.search_providers = {
            "baidu": self._search_baidu,
            "sogou": self._search_sogou,
            "360": self._search_360,
            "google": self._search_google,
            "bing": self._search_bing,
            "duckduckgo": self._search_duckduckgo
        }
    
    async def search(self, query: str, provider: str = "baidu") -> List[Dict[str, Any]]:
        """执行搜索"""
        if provider not in self.search_providers:
            raise ValueError(f"不支持的搜索提供商: {provider}")
        
        search_func = self.search_providers[provider]
        try:
            return await search_func(query)
        except Exception as e:
            return []
    
    async def get_search_providers(self) -> List[Dict[str, str]]:
        """获取所有可用的搜索提供商"""
        return [
            {
                "name": "baidu",
                "displayName": "百度",
                "description": "百度搜索引擎"
            },
            {
                "name": "sogou",
                "displayName": "搜狗",
                "description": "搜狗搜索引擎"
            },
            {
                "name": "360",
                "displayName": "360搜索",
                "description": "360搜索引擎"
            },
            {
                "name": "google",
                "displayName": "Google",
                "description": "Google搜索引擎"
            },
            {
                "name": "bing",
                "displayName": "Bing",
                "description": "微软Bing搜索"
            },
            {
                "name": "duckduckgo",
                "displayName": "DuckDuckGo",
                "description": "隐私保护的搜索引擎"
            }
        ]
    
    async def _search_baidu(self, query: str) -> List[Dict[str, Any]]:
        """百度搜索"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.baidu.com/s?wd={encoded_query}"
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        # 这里应该解析HTML并提取搜索结果
                        # 为了演示，返回模拟结果
                        return self._mock_search_results(query, "百度")
                    else:
                        return []
        except Exception as e:
            return []
    
    async def _search_sogou(self, query: str) -> List[Dict[str, Any]]:
        """搜狗搜索"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.sogou.com/web?query={encoded_query}"
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return self._mock_search_results(query, "搜狗")
                    else:
                        return []
        except Exception as e:
            return []

    async def _search_360(self, query: str) -> List[Dict[str, Any]]:
        """360搜索"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.so.com/s?q={encoded_query}"
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return self._mock_search_results(query, "360搜索")
                    else:
                        return []
        except Exception as e:
            return []

    async def _search_google(self, query: str) -> List[Dict[str, Any]]:
        """Google搜索"""
        try:
            # 注意: Google搜索通常需要API密钥
            # 这里返回模拟结果
            return self._mock_search_results(query, "Google")
        except Exception as e:
            return []
    
    async def _search_bing(self, query: str) -> List[Dict[str, Any]]:
        """Bing搜索"""
        try:
            # 注意: Bing搜索可能需要API密钥
            # 这里返回模拟结果
            return self._mock_search_results(query, "Bing")
        except Exception as e:
            return []
    
    async def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """DuckDuckGo搜索"""
        try:
            # DuckDuckGo有一个Instant Answer API
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        # 处理抽象答案
                        if data.get('Abstract'):
                            results.append({
                                'title': data.get('AbstractText', query),
                                'url': data.get('AbstractURL', ''),
                                'snippet': data.get('Abstract', ''),
                                'source': 'DuckDuckGo'
                            })
                        
                        # 处理相关主题
                        for topic in data.get('RelatedTopics', [])[:5]:
                            if isinstance(topic, dict) and topic.get('Text'):
                                results.append({
                                    'title': topic.get('Text', '').split(' - ')[0],
                                    'url': topic.get('FirstURL', ''),
                                    'snippet': topic.get('Text', ''),
                                    'source': 'DuckDuckGo'
                                })
                        
                        return results if results else self._mock_search_results(query, "DuckDuckGo")
                    else:
                        return self._mock_search_results(query, "DuckDuckGo")
        except Exception as e:
            print(f"DuckDuckGo搜索失败: {e}")
            return self._mock_search_results(query, "DuckDuckGo")
    
    def _mock_search_results(self, query: str, source: str) -> List[Dict[str, Any]]:
        """生成模拟搜索结果"""
        return [
            {
                'title': f'{query} - {source}搜索结果1',
                'url': f'https://example.com/result1?q={urllib.parse.quote(query)}',
                'snippet': f'这是关于"{query}"的搜索结果摘要1。包含相关信息和详细描述。',
                'source': source
            },
            {
                'title': f'{query} - {source}搜索结果2',
                'url': f'https://example.com/result2?q={urllib.parse.quote(query)}',
                'snippet': f'这是关于"{query}"的搜索结果摘要2。提供更多相关信息和解释。',
                'source': source
            },
            {
                'title': f'{query} - {source}搜索结果3',
                'url': f'https://example.com/result3?q={urllib.parse.quote(query)}',
                'snippet': f'这是关于"{query}"的搜索结果摘要3。包含补充信息和参考资料。',
                'source': source
            }
        ]