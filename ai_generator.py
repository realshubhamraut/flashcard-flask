import os
import json
from typing import Dict, List, Optional
import google.generativeai as genai

# Syllabus module definitions (textbook order for Shubham)
SYLLABUS_MODULES = {
    "Linux Programming": {
        "hours": 40,
        "topics": [
            "Installation (Ubuntu and CentOS)",
            "Basics of Linux",
            "Configuring Linux",
            "Shells, Commands, and Navigation",
            "Common Text Editors",
            "Administering Linux",
            "Introduction to Users and Groups",
            "Linux Shell Scripting",
            "Shell Computing",
            "Introduction to Enterprise Computing",
            "Remote Access"
        ]
    },
    "Introduction to Git/GitHub/GitLab": {
        "hours": 20,
        "topics": [
            "Introduction to Version Control Systems",
            "Creating GitHub Repository",
            "Using Git – Core Commands",
            "Creating Projects on GitHub and GitLab",
            "Managing Code Repositories"
        ]
    },
    "Introduction to Cloud Computing": {
        "hours": 40,
        "topics": [
            "Cloud Computing Basics",
            "Understanding Cloud Vendors (AWS EC2, Lambda, Azure VMs, Azure Data Factory)",
            "Definition, Characteristics, and Components",
            "Cloud Provider Landscape",
            "Software as a Service (SaaS)",
            "Platform as a Service (PaaS)",
            "Infrastructure as a Service (IaaS)",
            "Organizational Cloud Scenarios",
            "Benefits and Limitations",
            "Deploying Applications over Cloud",
            "Comparison of SaaS, PaaS, and IaaS",
            "Cloud Products and Solutions",
            "Compute Products and Services",
            "Elastic Cloud Compute",
            "Working with Cloud Dashboards",
            "Deploying AI and Analytics Workloads"
        ]
    },
    "Python Programming": {
        "hours": 80,
        "topics": [
            "Python Basics",
            "If, If-Else, and Nested If-Else",
            "Looping Constructs (For, While, Nested)",
            "Control Structures",
            "Break, Continue, and Pass",
            "Strings and Tuples",
            "Accessing Strings",
            "String Operations and Slices",
            "Working with Lists",
            "List Operations, Functions, and Methods",
            "Files and Pickling",
            "Modules",
            "Dictionaries",
            "Dictionary Comprehension",
            "Functions and Functional Programming",
            "Managing Values in Lists",
            "Introducing Tuples",
            "Matplotlib and Seaborn Visualization",
            "OOP Concepts",
            "Classes and Objects",
            "Attributes and Methods",
            "Inheritance",
            "Overloading and Overriding",
            "Data Hiding",
            "Generators",
            "Decorators",
            "Exception Handling",
            "Except and Try-Finally Clauses",
            "User Defined Exceptions",
            "Data Wrangling",
            "Data Cleaning",
            "Loading Images and Audio with Python Libraries",
            "Creating Python Virtual Environments",
            "Logging in Python"
        ]
    },
    "R Programming": {
        "hours": 60,
        "topics": [
            "Reading and Getting Data into R",
            "Exporting Data from R",
            "Data Objects, Types, and Structures",
            "Viewing Named Objects",
            "Structure of Data Items",
            "Manipulating and Processing Data in R",
            "Creating and Sorting Data Frames",
            "Extracting, Combining, Merging, and Reshaping Data Frames",
            "Control Structures",
            "Functions in R (Numeric, Character, Statistical)",
            "Working with Objects",
            "Viewing Objects within Objects",
            "Constructing Data Objects",
            "Packages – Tidyverse, dplyr, tidyr",
            "Queuing Theory",
            "Applied Case Study"
        ]
    },
    "Java Programming and JVM": {
        "hours": 60,
        "topics": [
            "Introduction to Java Virtual Machine",
            "Data Types, Operators, and Language Basics",
            "OOP Concepts",
            "Program Constructs",
            "Inner Classes and Inheritance",
            "Interfaces and Packages",
            "Exception Handling",
            "Collections Framework",
            "Threads",
            "java.lang Package",
            "java.util Package",
            "Lambda Expressions",
            "Introduction to Streams",
            "Introduction to JDBC API"
        ]
    },
    "Business Analytics and Statistics": {
        "hours": 100,
        "topics": [
            "Introduction to Business Analytics using Case Studies",
            "Summary Statistics",
            "Making Right Business Decisions",
            "Foundational Statistical Concepts",
            "Descriptive Statistics and Measures",
            "Probability Theory",
            "Probability Distributions (Normal, Binomial, Poisson)",
            "Sampling and Estimation",
            "Statistical Interfaces",
            "Predictive Modelling and Analysis",
            "Bayes' Theorem",
            "Central Limit Theorem",
            "Statistical Inference Terminology",
            "Hypothesis Testing",
            "Parametric Tests (ANOVA, t-test)",
            "Non-Parametric Tests (Chi-Square, U-Test)",
            "Data Exploration and Preparation",
            "Correlation and Covariance",
            "Handling Outliers",
            "Simulation and Risk Analysis",
            "Optimization (Linear and Integer)",
            "Overview of Factor Analysis",
            "Directional Data Analytics",
            "Functional Data Analysis",
            "Predictive Modelling from Correlation to Segmentation",
            "Identifying Informative Attributes",
            "Progressive Attributive Segmentation",
            "Model Induction and Prediction",
            "Supervised Segmentation",
            "Visualizing Segmentations",
            "Decision Trees as Rule Sets",
            "Probability Estimation",
            "Decision Analytics and Evaluating Classifiers",
            "Analytical Frameworks and Baselines",
            "Investment Implications from Performance",
            "Evidence and Probabilities with Bayes' Rule",
            "Probabilistic Reasoning",
            "Business Strategy: Achieving Competitive Advantages",
            "Sustaining Competitive Advantages"
        ]
    },
    "Python Libraries and Data Tools": {
        "hours": 20,
        "topics": [
            "Pandas",
            "NumPy",
            "Scrapy",
            "Plotly",
            "Beautiful Soup"
        ]
    },
    "Database Concepts and Data Management": {
        "hours": 90,
        "topics": [
            "Database Concepts (File System vs DBMS)",
            "OLAP vs OLTP",
            "Database Storage Structures",
            "Structured and Unstructured Data",
            "SQL Commands (DDL, DML, DCL)",
            "Stored Functions and Procedures",
            "Conditional Constructs in SQL",
            "Data Collection Techniques",
            "Designing Database Schema",
            "Normal Forms and ER Diagrams",
            "Relational Database Modelling",
            "Stored Procedures",
            "Triggers",
            "Systematic Data Gathering Tools",
            "Data Warehousing Concepts",
            "NoSQL Overview",
            "Data Models (XML, etc.)",
            "Working with MongoDB",
            "Cassandra Overview",
            "Comparing Cassandra with MongoDB",
            "Working with Cassandra",
            "Connecting Databases with Python",
            "Introduction to Data Driven Decisions",
            "Enterprise Data Management",
            "Data Preparation and Cleaning Techniques"
        ]
    },
    "Understanding Data Lakes": {
        "hours": 40,
        "topics": [
            "Data Lake Concepts",
            "Architecture and Components",
            "Data Lake vs Data Warehouse vs Lakehouse",
            "Data Storage Management",
            "Processing and Transformation",
            "Workflow Orchestration",
            "Analytics in Data Lakes",
            "Delta Lake Case Study"
        ]
    },
    "Introduction to Big Data": {
        "hours": 30,
        "topics": [
            "Big Data Beyond the Hype",
            "Big Data Skills and Sources",
            "Big Data Adoption",
            "Research Trends in Data Repositories",
            "Data Sharing and Reuse Practices",
            "Implications for Repository Data Curation"
        ]
    },
    "Hadoop Fundamentals": {
        "hours": 90,
        "topics": [
            "Introduction to Hadoop Programming",
            "Hadoop Ecosystem and Stack",
            "Hadoop Distributed File System (HDFS)",
            "Components of Hadoop",
            "Design of HDFS",
            "Java Interfaces to HDFS",
            "Architecture Overview",
            "Development Environment",
            "Hadoop Distributions and Commands",
            "Eclipse Development",
            "HDFS Command Line and Web Interfaces",
            "HDFS Java API",
            "Analyzing Data with Hadoop",
            "Scaling Out",
            "Hadoop Event Stream Processing",
            "Complex Event Processing",
            "MapReduce Introduction",
            "Developing a MapReduce Application",
            "How MapReduce Works",
            "MapReduce Job Anatomy",
            "Failure Handling",
            "Job Scheduling",
            "Shuffle and Sort",
            "Task Execution",
            "MapReduce Types and Formats",
            "MapReduce Features",
            "Real-World MapReduce"
        ]
    },
    "Hadoop Environment and Administration": {
        "hours": 50,
        "topics": [
            "Setting up a Hadoop Cluster",
            "Cluster Specification",
            "Cluster Setup and Installation",
            "Hadoop Configuration",
            "Security in Hadoop",
            "Administering Hadoop",
            "HDFS Monitoring and Maintenance",
            "Hadoop Benchmarks"
        ]
    },
    "Apache Airflow and ETL Informatica": {
        "hours": 30,
        "topics": [
            "Introduction to Data Warehousing",
            "Introduction to Data Lakes",
            "Designing Data Warehousing for ETL Pipelines",
            "Designing Data Lakes for ETL Pipelines",
            "ETL vs ELT"
        ]
    },
    "Introduction to Hive": {
        "hours": 40,
        "topics": [
            "Programming with Hive",
            "Hive as a Data Warehouse System",
            "Optimizing with Combiners",
            "Bucketing Techniques",
            "Sorting, Indexing, and Searching",
            "Map-Side and Reduce-Side Joins",
            "Hive Evolution and Purpose",
            "Case Studies on Ingestion and Warehousing"
        ]
    },
    "HBase": {
        "hours": 30,
        "topics": [
            "HBase Overview",
            "Architecture Comparison",
            "HBase Java Client API",
            "CRUD Operations in HBase",
            "Security in HBase"
        ]
    },
    "Apache Spark": {
        "hours": 80,
        "topics": [
            "Spark Overview",
            "APIs for Large-Scale Data Processing",
            "Linking with Spark",
            "Initializing Spark",
            "Resilient Distributed Datasets (RDDs)",
            "External Datasets",
            "RDD Operations",
            "Passing Functions to Spark",
            "Job Optimization",
            "Working with Key-Value Pairs",
            "Shuffle Operations",
            "RDD Persistence",
            "Removing Data from RDDs",
            "Shared Variables",
            "Exploratory Data Analysis using PySpark",
            "Deploying to a Cluster",
            "Spark Streaming",
            "Spark MLlib and ML APIs",
            "Spark DataFrames and Spark SQL",
            "Integrating Spark and Kafka",
            "Setting up Kafka Producers and Consumers",
            "Kafka Connect API",
            "MapReduce Integration",
            "Connecting Databases with Spark"
        ]
    },
    "Business Intelligence and Visualization": {
        "hours": 50,
        "topics": [
            "Business Intelligence Requirements",
            "Information Visualization Principles",
            "Data Analytics Life Cycle",
            "Analytic Processes and Tools",
            "Analysis vs Reporting",
            "Microsoft Excel Functions and Formulas",
            "Charts, Pivots, and Lookups",
            "Data Analysis Toolpak",
            "Descriptive Summaries",
            "Correlation and Regression",
            "Introduction to Tableau",
            "Data Sources in Tableau",
            "Taxonomy of Data Visualization",
            "Numeric, String, and Date Calculations",
            "Level of Detail (LOD) Expressions",
            "Modern Data Analytics Tools",
            "Visualization Techniques"
        ]
    },
    "Machine Learning": {
        "hours": 100,
        "topics": [
            "Introduction to Machine Learning",
            "Formal Learning Model – PAC Learning",
            "Bias-Complexity Trade-off",
            "VC Dimension",
            "Non-Uniform Learnability",
            "Structural Risk Minimization",
            "Occam's Razor",
            "No Free Lunch Theorem",
            "Regularization and Stability",
            "Model Selection and Validation",
            "Machine Learning Taxonomy",
            "Supervised Learning",
            "Unsupervised Learning",
            "Semi-Supervised Learning",
            "Practical Machine Learning Use Cases",
            "Clustering (K-Means and Variants)",
            "Hierarchical Clustering",
            "Dimensionality Reduction (PCA, Kernel PCA, LDA, Random Projections)",
            "Fundamentals of Information Theory",
            "Classification and Regression Techniques",
            "k-Nearest Neighbors",
            "Decision Trees",
            "Bayesian Analysis",
            "Naive Bayes Classifier",
            "Random Forest",
            "Gradient Boosting Machines",
            "Support Vector Machines",
            "XGBoost",
            "CatBoost",
            "Linear and Non-Linear Regression",
            "Time Series Forecasting"
        ]
    },
    "Deep Learning": {
        "hours": 90,
        "topics": [
            "Introduction to Neural Networks",
            "Neurons and Network Construction",
            "Backpropagation",
            "Deep Feedforward Networks",
            "Regularization for Deep Learning",
            "Optimization for Training Deep Models",
            "Convolutional Neural Networks",
            "Sequence Modelling using Recurrent Neural Networks",
            "Transfer Learning",
            "Autoencoders",
            "Object Detection",
            "Object Segmentation and Tracking",
            "Concepts of Natural Language Processing"
        ]
    },
    "Generative AI": {
        "hours": 60,
        "topics": [
            "Introduction to Transformers",
            "Encoder, Decoder, and Encoder-Decoder Architectures",
            "Attention Mechanisms",
            "Overview of BERT",
            "Applications of Transformers",
            "Introduction to Large Language Models",
            "Understanding and Handling Text Data",
            "Fine-Tuning Pre-Trained Models",
            "Reward Models and Alignment Strategies",
            "Practical Case Studies using SLMs and LLMs",
            "Deployment of LLMs"
        ]
    }
}

SYLLABUS_MODULE_SEQUENCE = list(SYLLABUS_MODULES.keys())

class GeminiFlashcardGenerator:
    def __init__(self, api_key: str = None):
        """Initialize the Gemini API client"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable must be set")
        
        # Configure the API
        genai.configure(api_key=self.api_key)
    
    def generate_flashcards(self, module: str, topics = None, count: int = 5, difficulty: str = "medium") -> dict:
        """Generate flashcards for a specific module and topic(s)
        
        Args:
            module: Module name
            topics: Single topic string, list of topics, or None for all topics
            count: Number of cards to generate
            difficulty: Difficulty level (easy, medium, hard)
        """
        
        if module not in SYLLABUS_MODULES:
            raise ValueError(f"Module '{module}' not found in syllabus")
        
        module_info = SYLLABUS_MODULES[module]
        
        # Handle topics parameter (can be string, list, or None)
        if topics is None or (isinstance(topics, list) and len(topics) == 0):
            topic_context = ""
        elif isinstance(topics, list):
            topic_context = f" focusing on: {', '.join(topics)}"
        else:
            topic_context = f" focusing on {topics}"
        
        prompt = f"""Generate {count} multiple-choice flashcards for {module}{topic_context}.

Difficulty level: {difficulty}
Module context: {', '.join(module_info['topics'][:10])}...

Generate flashcards in this EXACT JSON format (return ONLY pure JSON, no markdown formatting):
{{
  "name": "{module}{topic_context}",
  "description": "Fundamental concepts for this topic",
  "cards": [
    {{
      "question": "What is a list in Python?",
      "hint": "It's a built-in data structure",
      "options": [
        "A key-value pair structure",
        "An ordered collection of items",
        "A function decorator",
        "A class attribute"
      ],
      "correct_answer": 1,
      "description": "A list is an ordered, mutable collection of items in Python. Lists can contain elements of different types and support various operations like indexing, slicing, and iteration.",
      "reference": "https://docs.python.org/3/tutorial/datastructures.html",
      "code": "my_list = [1, 2, 3]\\nprint(my_list[0])  # Output: 1"
    }}
  ]
}}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown code blocks (```), no extra text
2. "options" MUST be an array of exactly 4 strings
3. "correct_answer" MUST be an integer (0, 1, 2, or 3) - the index of the correct option
4. "code" should contain actual code examples when relevant (use \\n for newlines), or empty string ""
5. "hint" should help without revealing the answer
6. "description" should explain WHY the answer is correct and why others are wrong
7. All string fields are required (use "" for empty values)
8. Difficulty '{difficulty}': {"basic syntax and definitions" if difficulty == "easy" else "practical scenarios and applications" if difficulty == "medium" else "complex problems and edge cases"}

Return the JSON object directly - no formatting, no code blocks."""

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                # Remove first line (```) and last line (```)
                response_text = '\n'.join(lines[1:-1])
                # Remove 'json' if it's the first word
                if response_text.strip().startswith('json'):
                    response_text = response_text.strip()[4:].strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate format
            if 'cards' not in result:
                return {'success': False, 'error': 'Invalid response format: missing cards'}
            
            # Validate each card
            valid_cards = []
            for card in result['cards']:
                if (isinstance(card.get('options'), list) and 
                    len(card.get('options', [])) == 4 and
                    isinstance(card.get('correct_answer'), int) and
                    0 <= card.get('correct_answer', -1) <= 3):
                    valid_cards.append(card)
            
            if not valid_cards:
                return {'success': False, 'error': 'No valid cards in response'}
            
            topic_str = ', '.join(topics) if isinstance(topics, list) else (topics or "")
            
            return {
                'success': True,
                'cards': valid_cards,
                'module': module,
                'topic': topic_str,
                'deck_name': result.get('name', f"{module}{topic_context}"),
                'deck_description': result.get('description', '')
            }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Invalid JSON response: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
