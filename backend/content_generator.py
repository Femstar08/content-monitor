"""
Content generation service using extracted AWS data
"""
import re
from typing import List, Dict, Any
from datetime import datetime


class ContentGenerator:
    """Generate various types of content from extracted AWS data."""
    
    def __init__(self):
        self.aws_services = {
            'ec2': 'Amazon Elastic Compute Cloud',
            's3': 'Amazon Simple Storage Service',
            'lambda': 'AWS Lambda',
            'rds': 'Amazon Relational Database Service',
            'vpc': 'Amazon Virtual Private Cloud',
            'iam': 'AWS Identity and Access Management',
            'cloudformation': 'AWS CloudFormation',
            'cloudwatch': 'Amazon CloudWatch'
        }
    
    def generate_blog_post(self, sources: List[Dict[str, Any]], topic: str = "") -> Dict[str, Any]:
        """Generate a blog post from source materials."""
        # Analyze sources
        analysis = self._analyze_sources(sources)
        
        # Generate title
        if topic:
            title = f"AWS {topic.title()}: {self._generate_subtitle(analysis)}"
        else:
            main_topic = analysis['top_topics'][0]['topic'] if analysis['top_topics'] else 'Services'
            title = f"AWS {main_topic.title()}: {self._generate_subtitle(analysis)}"
        
        # Generate content sections
        sections = self._generate_blog_sections(analysis, sources)
        
        return {
            "type": "blog_post",
            "title": title,
            "meta_description": self._generate_meta_description(analysis, topic),
            "sections": sections,
            "tags": [t['topic'] for t in analysis['top_topics'][:8]],
            "word_count": analysis['total_words'],
            "reading_time": max(1, analysis['total_words'] // 200),
            "sources_count": len(sources),
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_technical_guide(self, sources: List[Dict[str, Any]], topic: str = "") -> Dict[str, Any]:
        """Generate a technical implementation guide."""
        analysis = self._analyze_sources(sources)
        
        title = f"AWS {topic.title()} Implementation Guide" if topic else "AWS Implementation Guide"
        
        # Generate structured guide sections
        guide_sections = [
            {
                "title": "Overview",
                "content": self._generate_overview(analysis, topic),
                "type": "overview"
            },
            {
                "title": "Prerequisites",
                "content": self._generate_prerequisites(analysis),
                "type": "prerequisites"
            },
            {
                "title": "Implementation Steps",
                "content": self._generate_implementation_steps(analysis, topic),
                "type": "steps"
            },
            {
                "title": "Best Practices",
                "content": self._generate_best_practices(analysis),
                "type": "best_practices"
            },
            {
                "title": "Troubleshooting",
                "content": self._generate_troubleshooting(analysis),
                "type": "troubleshooting"
            }
        ]
        
        return {
            "type": "technical_guide",
            "title": title,
            "sections": guide_sections,
            "difficulty": self._assess_difficulty(analysis),
            "estimated_time": self._estimate_implementation_time(analysis),
            "aws_services": self._extract_aws_services(analysis),
            "sources_count": len(sources),
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_summary_report(self, sources: List[Dict[str, Any]], topic: str = "") -> Dict[str, Any]:
        """Generate an executive summary report."""
        analysis = self._analyze_sources(sources)
        
        title = f"AWS {topic.title()} Summary Report" if topic else "AWS Content Summary Report"
        
        return {
            "type": "summary_report",
            "title": title,
            "executive_summary": self._generate_executive_summary(analysis, topic),
            "key_findings": self._generate_key_findings(analysis),
            "recommendations": self._generate_recommendations(analysis),
            "metrics": {
                "sources_analyzed": len(sources),
                "total_content_length": analysis['total_words'],
                "top_topics": analysis['top_topics'][:5],
                "content_types": analysis['content_types']
            },
            "generated_at": datetime.now().isoformat()
        }
    
    def _analyze_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze source materials to extract key information."""
        total_words = 0
        all_topics = {}
        content_types = {}
        key_phrases = []
        
        for source in sources:
            # Count words
            text = source.get('text_content', '') + ' ' + source.get('summary', '')
            words = len(text.split())
            total_words += words
            
            # Aggregate topics
            if source.get('topics'):
                for topic_item in source['topics']:
                    topic = topic_item.get('topic', '')
                    mentions = topic_item.get('mentions', 0)
                    all_topics[topic] = all_topics.get(topic, 0) + mentions
            
            # Count content types
            content_type = source.get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
            
            # Extract key phrases
            if source.get('summary'):
                key_phrases.extend(self._extract_key_phrases(source['summary']))
        
        # Sort topics by mentions
        top_topics = [{"topic": k, "mentions": v} for k, v in 
                     sorted(all_topics.items(), key=lambda x: x[1], reverse=True)]
        
        return {
            "total_words": total_words,
            "top_topics": top_topics,
            "content_types": content_types,
            "key_phrases": list(set(key_phrases))[:20]  # Top 20 unique phrases
        }
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text."""
        # Simple phrase extraction - look for AWS-related terms
        aws_patterns = [
            r'AWS \w+', r'Amazon \w+', r'best practice\w*', r'security \w+',
            r'architecture \w+', r'implementation \w+', r'configuration \w+'
        ]
        
        phrases = []
        for pattern in aws_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            phrases.extend(matches)
        
        return phrases
    
    def _generate_subtitle(self, analysis: Dict[str, Any]) -> str:
        """Generate a subtitle based on analysis."""
        if analysis['top_topics']:
            main_topic = analysis['top_topics'][0]['topic']
            if 'security' in main_topic.lower():
                return "Security Best Practices and Implementation Guide"
            elif 'architecture' in main_topic.lower():
                return "Architecture Patterns and Design Principles"
            elif 'performance' in main_topic.lower():
                return "Performance Optimization and Monitoring"
            else:
                return "Best Practices and Implementation Guide"
        return "Comprehensive Guide and Best Practices"
    
    def _generate_meta_description(self, analysis: Dict[str, Any], topic: str) -> str:
        """Generate meta description for SEO."""
        topics = [t['topic'] for t in analysis['top_topics'][:3]]
        topic_str = ', '.join(topics) if topics else 'AWS services'
        
        return f"Comprehensive guide to AWS {topic or topic_str} covering best practices, implementation strategies, and expert recommendations based on official AWS documentation."
    
    def _generate_blog_sections(self, analysis: Dict[str, Any], sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate blog post sections."""
        sections = []
        
        # Introduction
        sections.append({
            "title": "Introduction",
            "content": f"This comprehensive guide explores AWS best practices and implementation strategies based on analysis of {len(sources)} official AWS sources. We'll cover key topics including {', '.join([t['topic'] for t in analysis['top_topics'][:3]])}.",
            "type": "introduction"
        })
        
        # Main content sections based on top topics
        for i, topic_item in enumerate(analysis['top_topics'][:3]):
            topic = topic_item['topic']
            sections.append({
                "title": f"{topic.title()} Best Practices",
                "content": self._generate_topic_content(topic, sources),
                "type": "main_content"
            })
        
        # Conclusion
        sections.append({
            "title": "Conclusion",
            "content": f"Implementing these AWS best practices will help ensure your cloud infrastructure is secure, scalable, and cost-effective. Regular review of AWS documentation and staying updated with new services and features is essential for maintaining optimal performance.",
            "type": "conclusion"
        })
        
        return sections
    
    def _generate_topic_content(self, topic: str, sources: List[Dict[str, Any]]) -> str:
        """Generate content for a specific topic."""
        # Find sources that mention this topic
        relevant_sources = []
        for source in sources:
            if source.get('topics'):
                for topic_item in source['topics']:
                    if topic_item.get('topic', '').lower() == topic.lower():
                        relevant_sources.append(source)
                        break
        
        if not relevant_sources:
            return f"AWS {topic} is a critical component of cloud infrastructure that requires careful planning and implementation."
        
        # Generate content based on relevant sources
        content = f"Based on AWS documentation and best practices, {topic} implementation should focus on:\n\n"
        
        # Add key points from sources
        for source in relevant_sources[:2]:  # Use top 2 relevant sources
            if source.get('summary'):
                content += f"• {source['summary'][:200]}...\n"
        
        return content
    
    def _generate_overview(self, analysis: Dict[str, Any], topic: str) -> str:
        """Generate overview section for technical guide."""
        return f"This implementation guide covers AWS {topic or 'services'} deployment and configuration. Based on official AWS documentation and best practices, this guide provides step-by-step instructions for successful implementation."
    
    def _generate_prerequisites(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate prerequisites list."""
        return [
            "AWS account with appropriate permissions",
            "AWS CLI installed and configured",
            "Basic understanding of AWS services",
            "Familiarity with cloud architecture principles"
        ]
    
    def _generate_implementation_steps(self, analysis: Dict[str, Any], topic: str) -> List[Dict[str, str]]:
        """Generate implementation steps."""
        return [
            {
                "step": 1,
                "title": "Planning and Design",
                "description": "Define requirements and design architecture"
            },
            {
                "step": 2,
                "title": "Environment Setup",
                "description": "Configure AWS environment and prerequisites"
            },
            {
                "step": 3,
                "title": "Implementation",
                "description": f"Deploy and configure AWS {topic or 'services'}"
            },
            {
                "step": 4,
                "title": "Testing and Validation",
                "description": "Test implementation and validate functionality"
            },
            {
                "step": 5,
                "title": "Monitoring and Optimization",
                "description": "Set up monitoring and optimize performance"
            }
        ]
    
    def _generate_best_practices(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate best practices list."""
        practices = [
            "Follow AWS Well-Architected Framework principles",
            "Implement proper security controls and access management",
            "Use Infrastructure as Code for reproducible deployments",
            "Set up comprehensive monitoring and alerting",
            "Implement cost optimization strategies"
        ]
        
        # Add topic-specific practices
        for topic_item in analysis['top_topics'][:3]:
            topic = topic_item['topic']
            if 'security' in topic.lower():
                practices.append("Enable encryption at rest and in transit")
            elif 'performance' in topic.lower():
                practices.append("Implement auto-scaling and load balancing")
        
        return practices
    
    def _generate_troubleshooting(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate troubleshooting guide."""
        return [
            {
                "issue": "Service connectivity problems",
                "solution": "Check security groups, NACLs, and routing tables"
            },
            {
                "issue": "Performance issues",
                "solution": "Review CloudWatch metrics and optimize resource allocation"
            },
            {
                "issue": "Access denied errors",
                "solution": "Verify IAM permissions and resource policies"
            }
        ]
    
    def _assess_difficulty(self, analysis: Dict[str, Any]) -> str:
        """Assess implementation difficulty."""
        topic_count = len(analysis['top_topics'])
        if topic_count <= 3:
            return "Beginner"
        elif topic_count <= 6:
            return "Intermediate"
        else:
            return "Advanced"
    
    def _estimate_implementation_time(self, analysis: Dict[str, Any]) -> str:
        """Estimate implementation time."""
        complexity = len(analysis['top_topics'])
        if complexity <= 3:
            return "2-4 hours"
        elif complexity <= 6:
            return "1-2 days"
        else:
            return "3-5 days"
    
    def _extract_aws_services(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract AWS services mentioned in content."""
        services = []
        for topic_item in analysis['top_topics']:
            topic = topic_item['topic'].lower()
            if topic in self.aws_services:
                services.append(self.aws_services[topic])
            elif any(service in topic for service in self.aws_services.keys()):
                for service_key, service_name in self.aws_services.items():
                    if service_key in topic:
                        services.append(service_name)
                        break
        
        return list(set(services))  # Remove duplicates
    
    def _generate_executive_summary(self, analysis: Dict[str, Any], topic: str) -> str:
        """Generate executive summary."""
        return f"Analysis of AWS {topic or 'documentation'} reveals key focus areas including {', '.join([t['topic'] for t in analysis['top_topics'][:3]])}. This report synthesizes information from multiple official AWS sources to provide actionable insights and recommendations."
    
    def _generate_key_findings(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate key findings."""
        findings = []
        
        for topic_item in analysis['top_topics'][:5]:
            topic = topic_item['topic']
            mentions = topic_item['mentions']
            findings.append(f"{topic.title()} is mentioned {mentions} times across sources, indicating high importance")
        
        return findings
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations."""
        return [
            "Prioritize implementation of high-frequency topics identified in the analysis",
            "Follow AWS Well-Architected Framework principles for all implementations",
            "Establish regular review cycles for AWS best practices and documentation updates",
            "Implement comprehensive monitoring and alerting for all AWS resources",
            "Consider cost optimization strategies throughout the implementation process"
        ]