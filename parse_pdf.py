#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析WIFI标签系统API接口PDF文档
"""

import os
import re
import json
from typing import List, Dict, Any, Optional
import pdfplumber

class WifiEslApiParser:
    """WIFI标签系统API接口文档解析器"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.all_text = ""
        self.pages_text = []
        self.api_sections = []
        self.metadata = {}
        
    def extract_text(self):
        """提取PDF中的文本内容"""
        print(f"正在读取PDF文件: {self.pdf_path}")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            # 获取文档信息
            self.metadata = {
                "total_pages": len(pdf.pages),
                "file_name": os.path.basename(self.pdf_path)
            }
            
            # 逐页提取文本
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    self.pages_text.append({
                        "page": i + 1,
                        "text": page_text,
                        "bbox": page.bbox
                    })
                    self.all_text += f"\n--- 第 {i+1} 页 ---\n{page_text}"
                    
            print(f"文档共 {len(pdf.pages)} 页，文本提取完成")
            
    def analyze_document_structure(self):
        """分析文档结构"""
        print("分析文档结构...")
        
        # 查找章节标题
        section_patterns = [
            r"第[一二三四五六七八九十\d]+章\s*[^\n]+",
            r"\d+\.\d+\s*[^\n]+",
            r"[一二三四五六七八九十]+、\s*[^\n]+",
            r"API接口\s*[^\n]*",
            r"接口说明\s*[^\n]*",
            r"请求参数\s*[^\n]*",
            r"返回参数\s*[^\n]*",
            r"错误码\s*[^\n]*"
        ]
        
        sections = []
        for page in self.pages_text:
            lines = page['text'].split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                    
                for pattern in section_patterns:
                    if re.match(pattern, line, re.IGNORECASE):
                        sections.append({
                            "page": page['page'],
                            "line_number": i,
                            "content": line,
                            "type": self._classify_section(line)
                        })
                        break
                        
        return sections
    
    def _classify_section(self, text: str) -> str:
        """分类章节类型"""
        text_lower = text.lower()
        
        if "api" in text_lower or "接口" in text_lower:
            return "api_section"
        elif "请求" in text_lower or "参数" in text_lower:
            return "request_section"
        elif "返回" in text_lower or "响应" in text_lower:
            return "response_section"
        elif "错误" in text_lower or "error" in text_lower:
            return "error_section"
        elif "协议" in text_lower or "协议" in text_lower:
            return "protocol_section"
        elif "概述" in text_lower or "简介" in text_lower:
            return "overview_section"
        elif "示例" in text_lower:
            return "example_section"
        elif "附录" in text_lower:
            return "appendix_section"
        elif "更新" in text_lower or "版本" in text_lower:
            return "version_section"
        else:
            return "other_section"
    
    def extract_api_interfaces(self):
        """提取API接口信息"""
        print("提取API接口信息...")
        
        # 查找API接口相关的部分
        api_patterns = [
            r"(POST|GET|PUT|DELETE)\s+[/\w]+",  # HTTP方法 + 路径
            r"接口名称[:：]\s*[^\n]+",
            r"接口地址[:：]\s*[^\n]+",
            r"接口描述[:：]\s*[^\n]+",
            r"功能说明[:：]\s*[^\n]+"
        ]
        
        apis = []
        current_api = {}
        
        # 逐页分析
        for page in self.pages_text:
            lines = page['text'].split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                    
                # 检查是否是新的API开始
                api_start = False
                for pattern in api_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        api_start = True
                        break
                
                if api_start:
                    # 保存前一个API
                    if current_api:
                        apis.append(current_api.copy())
                        current_api = {}
                    
                    # 开始新的API
                    current_api = {
                        "page": page['page'],
                        "line_start": i,
                        "details": {}
                    }
                
                # 收集API详情
                if current_api:
                    # 解析键值对
                    kv_patterns = [
                        r"([^:：]+)[:：]\s*(.+)",
                        r"([^:：]+)\s+[:：]\s*(.+)"
                    ]
                    
                    for pattern in kv_patterns:
                        match = re.match(pattern, line)
                        if match:
                            key = match.group(1).strip()
                            value = match.group(2).strip()
                            current_api["details"][key] = value
                            break
        
        # 添加最后一个API
        if current_api:
            apis.append(current_api)
            
        return apis
    
    def analyze_error_codes(self):
        """分析错误码"""
        print("分析错误码...")
        
        error_patterns = [
            r"错误码[:：]\s*(\d+)\s*错误描述[:：]\s*(.+)",
            r"(\d+)\s*[:：]\s*(.+)",
            r"错误\s*(\d+)[:：]\s*(.+)",
            r"code\s*(\d+)[:：]\s*(.+)"
        ]
        
        error_codes = []
        
        for page in self.pages_text:
            text = page['text']
            
            for pattern in error_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    error_codes.append({
                        "page": page['page'],
                        "code": match[0],
                        "description": match[1].strip(),
                        "type": self._classify_error(match[1])
                    })
        
        return error_codes
    
    def _classify_error(self, description: str) -> str:
        """分类错误类型"""
        desc_lower = description.lower()
        
        if "成功" in desc_lower or "ok" in desc_lower:
            return "success"
        elif "权限" in desc_lower or "授权" in desc_lower:
            return "auth_error"
        elif "参数" in desc_lower:
            return "param_error"
        elif "网络" in desc_lower or "连接" in desc_lower:
            return "network_error"
        elif "服务器" in desc_lower or "服务" in desc_lower:
            return "server_error"
        elif "设备" in desc_lower or "硬件" in desc_lower:
            return "device_error"
        elif "超时" in desc_lower:
            return "timeout_error"
        elif "不存在" in desc_lower or "未找到" in desc_lower:
            return "not_found_error"
        else:
            return "other_error"
    
    def generate_summary(self):
        """生成分析摘要"""
        print("生成分析摘要...")
        
        sections = self.analyze_document_structure()
        apis = self.extract_api_interfaces()
        error_codes = self.analyze_error_codes()
        
        summary = {
            "document_info": {
                "file_name": self.metadata.get("file_name", ""),
                "total_pages": self.metadata.get("total_pages", 0),
                "extracted_pages": len(self.pages_text),
                "text_length": len(self.all_text)
            },
            "structure_analysis": {
                "total_sections": len(sections),
                "section_types": self._count_section_types(sections),
                "main_sections": [s for s in sections if s["type"] != "other_section"]
            },
            "api_analysis": {
                "total_apis": len(apis),
                "api_summary": self._summarize_apis(apis)
            },
            "error_code_analysis": {
                "total_error_codes": len(error_codes),
                "error_types": self._count_error_types(error_codes)
            },
            "key_findings": self._extract_key_findings()
        }
        
        return summary
    
    def _count_section_types(self, sections: List[Dict]) -> Dict[str, int]:
        """统计章节类型"""
        counts = {}
        for section in sections:
            section_type = section["type"]
            counts[section_type] = counts.get(section_type, 0) + 1
        return counts
    
    def _summarize_apis(self, apis: List[Dict]) -> List[Dict]:
        """汇总API信息"""
        summaries = []
        for api in apis:
            details = api.get("details", {})
            summary = {
                "page": api.get("page"),
                "interface_name": details.get("接口名称", details.get("接口地址", "未命名接口")),
                "method": self._extract_http_method(details),
                "path": self._extract_api_path(details),
                "description": details.get("功能说明", details.get("接口描述", ""))
            }
            summaries.append(summary)
        return summaries
    
    def _extract_http_method(self, details: Dict[str, str]) -> str:
        """提取HTTP方法"""
        for key, value in details.items():
            if "方法" in key or "method" in key.lower():
                return value.upper()
        
        # 从接口地址中推测
        for value in details.values():
            if value.startswith(("GET ", "POST ", "PUT ", "DELETE ")):
                return value.split()[0].upper()
        
        return "未知"
    
    def _extract_api_path(self, details: Dict[str, str]) -> str:
        """提取API路径"""
        for key, value in details.items():
            if "地址" in key or "url" in key.lower() or "path" in key.lower():
                return value
        
        return "未知"
    
    def _count_error_types(self, error_codes: List[Dict]) -> Dict[str, int]:
        """统计错误类型"""
        counts = {}
        for error in error_codes:
            error_type = error["type"]
            counts[error_type] = counts.get(error_type, 0) + 1
        return counts
    
    def _extract_key_findings(self) -> List[str]:
        """提取关键发现"""
        findings = []
        
        # 分析文本内容寻找关键信息
        key_phrases = [
            "WIFI标签", "电子价签", "ESL", "无线通信", "AP", "基站",
            "固件升级", "批量操作", "实时更新", "价格同步", "库存管理",
            "商品管理", "门店管理", "用户管理", "权限管理", "设备管理"
        ]
        
        for phrase in key_phrases:
            if phrase in self.all_text:
                findings.append(f"文档包含'{phrase}'相关内容")
        
        # 检查是否有版本信息
        version_match = re.search(r"Ver[:\s]*([\d\.]+)", self.all_text, re.IGNORECASE)
        if version_match:
            findings.append(f"API接口版本: {version_match.group(1)}")
        
        # 检查是否有协议信息
        protocol_match = re.search(r"协议[:\s]*([^\n]+)", self.all_text)
        if protocol_match:
            findings.append(f"通信协议: {protocol_match.group(1)}")
        
        return findings
    
    def save_results(self, output_dir: str = "analysis_results"):
        """保存分析结果"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存原始文本
        with open(os.path.join(output_dir, "extracted_text.txt"), "w", encoding="utf-8") as f:
            f.write(self.all_text)
        
        # 保存分析摘要
        summary = self.generate_summary()
        with open(os.path.join(output_dir, "analysis_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 保存API接口详情
        apis = self.extract_api_interfaces()
        with open(os.path.join(output_dir, "api_interfaces.json"), "w", encoding="utf-8") as f:
            json.dump(apis, f, ensure_ascii=False, indent=2)
        
        # 保存错误码
        error_codes = self.analyze_error_codes()
        with open(os.path.join(output_dir, "error_codes.json"), "w", encoding="utf-8") as f:
            json.dump(error_codes, f, ensure_ascii=False, indent=2)
        
        print(f"分析结果已保存到目录: {output_dir}")
        
        return summary

def main():
    """主函数"""
    pdf_path = r"f:\pick\AI项目\CodeBuddy\WifiEsl\WIFI标签系统API接口Ver1.0.6.pdf"
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"错误: 文件不存在 - {pdf_path}")
        return
    
    # 创建解析器
    parser = WifiEslApiParser(pdf_path)
    
    # 提取文本
    parser.extract_text()
    
    # 生成并保存分析结果
    summary = parser.save_results()
    
    # 打印摘要
    print("\n" + "="*60)
    print("WIFI标签系统API接口文档分析摘要")
    print("="*60)
    
    doc_info = summary["document_info"]
    print(f"文档名称: {doc_info['file_name']}")
    print(f"总页数: {doc_info['total_pages']}")
    print(f"提取页数: {doc_info['extracted_pages']}")
    print(f"文本长度: {doc_info['text_length']} 字符")
    
    print(f"\n文档章节结构:")
    structure = summary["structure_analysis"]
    print(f"  总章节数: {structure['total_sections']}")
    for section_type, count in structure["section_types"].items():
        print(f"  {section_type}: {count}")
    
    print(f"\nAPI接口分析:")
    api_analysis = summary["api_analysis"]
    print(f"  发现API接口数: {api_analysis['total_apis']}")
    if api_analysis['total_apis'] > 0:
        print("  主要API接口:")
        for i, api in enumerate(api_analysis['api_summary'][:5], 1):
            print(f"    {i}. {api['method']} {api['path']} - {api['description'][:50]}...")
    
    print(f"\n错误码分析:")
    error_analysis = summary["error_code_analysis"]
    print(f"  错误码总数: {error_analysis['total_error_codes']}")
    for error_type, count in error_analysis['error_types'].items():
        print(f"  {error_type}: {count}")
    
    print(f"\n关键发现:")
    for finding in summary["key_findings"]:
        print(f"  * {finding}")
    
    print("\n" + "="*60)
    print("详细分析结果已保存到 'analysis_results' 目录")
    print("包括: extracted_text.txt, analysis_summary.json")
    print("      api_interfaces.json, error_codes.json")
    print("="*60)

if __name__ == "__main__":
    main()