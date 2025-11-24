import os
import json
from typing import Dict, List, Optional
from google import genai

# Syllabus module definitions
SYLLABUS_MODULES = {
    "Linux Programming": {
        "hours": 50,
        "topics": ["Installation (Ubuntu and CentOS)", "Basics of Linux", "Configuring Linux", "Shells, Commands, and Navigation", "Common Text Editors", "Administering Linux", "Users and Groups", "Linux shell scripting", "shell computing", "enterprise computing", "Remote access", "Git/GitHub/Gitlab", "Version control systems", "Cloud Computing Basics", "AWS EC2/Lambda", "Azure VMs", "Data Factory", "SAAS/PAAS/IAAS", "Deploy application over cloud"]
    },
    "Python Programming": {
        "hours": 80,
        "topics": ["Python basics", "If-else statements", "Nested if-else", "Looping (For, While)", "Control Structure", "Break/Continue/Pass", "Strings and Tuples", "Working with Lists", "Files and Pickling", "Modules", "Dictionaries", "Dictionary Comprehension", "Functions", "Functional Programming", "Lists and Tuples operations", "Matplotlib/Seaborn visualization", "OOPs concept", "Class and object", "Inheritance", "Overloading/Overriding", "Data hiding", "Generators", "Decorators", "Exception Handling", "Try-finally clause", "User Defined Exceptions", "Data wrangling", "Data cleaning", "Load images/audio with libraries", "Python virtual environment", "Logging in Python"]
    },
    "R Programming": {
        "hours": 70,
        "topics": ["Reading and Getting Data into R", "Exporting Data from R", "Data Objects-Data Types & Data Structure", "Viewing Named Objects", "Structure of Data Items", "Manipulating and Processing Data in R", "Creating/Accessing/sorting data frames", "Extracting/Combining/Merging/reshaping data frames", "Control Structures", "Functions in R (numeric, character, statistical)", "working with objects", "Viewing Objects within Objects", "Constructing Data Objects", "Packages - Tidyverse, Dplyr, Tidyr", "Queuing Theory", "Case Study"]
    },
    "Java Programming": {
        "hours": 70,
        "topics": ["Java Virtual Machine", "Data Types", "Operators and Language", "OOPs Concepts", "Constructs", "Inner Classes and Inheritance", "Interface and Package", "Exceptions", "Collections", "Threads", "Java.lang", "Java.util", "Lambda Expressions", "Introduction to Streams", "Introduction of JDBC API"]
    },
    "Advanced Analytics": {
        "hours": 90,
        "topics": ["Business Analytics case studies", "Summary Statistics", "Making Right Business Decisions", "Statistical Concepts", "Descriptive Statistics", "Probability theory", "Probability Distributions (Normal, Binomial, Poisson)", "Sampling and Estimation", "Statistical Interfaces", "Predictive modelling", "Bayes' Theorem", "Central Limit theorem", "Statistical Inference", "Hypothesis Testing", "Parametric Tests: ANOVA, t-test", "Non parametric Tests: chi-Square, U-Test", "Data Exploration & preparation", "Correlation", "Covariance", "Outliers", "Simulation and Risk Analysis", "Optimization", "Linear/Integer", "Factor Analysis", "Directional Data Analytics", "Functional Data Analysis", "Predictive Modelling", "Identifying Informative Attributes", "Supervised Segmentation", "Visualizing Segmentations", "Trees As Set Of Rules", "Probability Estimation", "Decision Analytics", "Evaluating Classifiers", "Evidence And Probabilities", "Bayes Rule", "Business Strategy", "Competitive Advantages", "Python Libraries - Pandas, Numpy, Scrapy, Plotly, Beautiful soup"]
    },
    "DBMS": {
        "hours": 90,
        "topics": ["Database Concepts (File System and DBMS)", "OLAP vs OLTP", "Database Storage Structures", "Structured and Unstructured data", "SQL Commands (DDL, DML, DCL)", "Stored functions and procedures", "Conditional Constructs in SQL", "data collection", "Designing Database schema", "Normal Forms and ER Diagram", "Relational Database modelling", "Stored Procedures", "Triggers", "Data gathering", "Data warehousing concept", "No-SQL", "Data Models - XML", "working with MongoDB", "Cassandra - overview", "comparison with MongoDB", "working with Cassandra", "Connecting DB's with Python", "Data Driven Decisions", "Enterprise Data Management", "data preparation and cleaning", "Understanding Data Lakes", "Data Lake architecture", "Data Lake vs. Data Warehouse vs. Lakehouse", "data storage management", "processing and transformation", "workflow orchestration", "analytics in Data Lake", "case study using Delta Lake"]
    },
    "Big Data Technologies": {
        "hours": 150,
        "topics": ["Introduction to Big Data", "Big Data Skills", "Sources Of Big Data", "Big Data Adoption", "Data Sharing and Reuse", "Hadoop Introduction", "The ecosystem and stack", "HDFS", "Components of Hadoop", "Design of HDFS", "Java interfaces to HDFS", "Architecture overview", "Development Environment", "Hadoop distribution", "basic commands", "Eclipse development", "HDFS command line and web interfaces", "HDFS Java API", "Analyzing Data with Hadoop", "Scaling Out", "event stream processing", "complex event processing", "MapReduce Introduction", "Developing MapReduce Application", "How MapReduce Works", "MapReduce Job run", "Failures", "Job Scheduling", "Shuffle and Sort", "Task execution", "MapReduce Types and Formats", "MapReduce Features", "Real-World MapReduce", "Hadoop Environment", "Setting up Hadoop Cluster", "Cluster specification", "Cluster Setup and Installation", "Hadoop Configuration", "Security in Hadoop", "Administering Hadoop", "HDFS Monitoring & Maintenance", "Hadoop benchmarks", "Apache Airflow/ETL Informatica", "Data warehousing", "Data lakes", "Designing Data warehousing for ETL", "Designing Data Lakes for ETL", "ETL vs ELT", "Introduction to HIVE", "Programming with Hive", "Data warehouse system for Hadoop", "Optimizing with Combiners", "Bucketing", "sorting, indexing and searching", "map-side and reduce-side joins", "evolution, purpose and use", "Case Studies on Ingestion", "HBase Overview", "comparison and architecture", "java client API", "CRUD operations", "security", "Apache Spark Overview", "APIs for large-scale data processing", "Linking with Spark", "Initializing Spark", "RDDs", "External Datasets", "RDD Operations", "Passing Functions to Spark", "Job optimization", "Working with Key-Value Pairs", "Shuffle operations", "RDD Persistence", "Removing Data", "Shared Variables", "EDA using PySpark", "Deploying to Cluster", "Spark Streaming", "Spark MLlib and ML APIs", "Spark Data Frames/Spark SQL", "Integration of Spark and Kafka", "Setting up Kafka Producer and Consumer", "Kafka Connect API", "Map reduce", "Connecting DB's with Spark"]
    },
    "Data Visualization": {
        "hours": 50,
        "topics": ["Business Intelligence - requirements, content and managements", "information Visualization", "Data analytics Life Cycle", "Analytic Processes and Tools", "Analysis vs. Reporting", "MS Excel: Functions, Formula, charts, Pivots and Lookups", "Data Analysis Tool pack", "Descriptive Summaries", "Correlation", "Regression", "Introduction to Tableau", "Data sources in Tableau", "Taxonomy of data visualization", "Numeric, String, Date Calculations", "LOD (Level of Detail) Expressio    },
    "Data Visualization": {
        "hours": 50,
        "topics": ["Business Intelligence - requirements, content and managements", "information Visualization", "Data analytics Life Cycle", "Analytic Processes and Tools", "Analysis vs. Reporting", "MS Excel: Functions, Formula, charts, Pivots rnability", "Structural risk minimization", "Occam's Razor", "No Free Lunch Theorem", "Regularization and Stability", "Model Selection and Validation", "Machine Learning taxonomy", "Supervised Learning", "Unsupervised Learning", "Semi-supervised Learning", "practical use cases of ML", "Clustering (K-Means and variants)", "Hierarchical Clustering", "Dimension Reduction (PCA, Kernel PCA, LDA, Random Projections)", "Fundamentals of information theory", "Classification and Regression", "KNN", "Decision Trees", "Bayesian analysis", "Naïve Bayes classifier", "Random forest", "Gradient boosting Machines", "SVM", "XGBoost", "CatBoost", "Linear and Non-linear regression", "Time series Forecasting", "Introduction to neural networks", "Neurons", "construction of networks", "backpropagation", "Deep Feedforward Networks", "Regularization for Deep Learning", "Optimization for Training Deep Models", "Convolutional Neural Networks", "Sequence modelling using RNNs", "Transfer Learning", "Autoencoders", "Object Detection", "Object Segmentation and Tracking", "Concepts of NLP", "Introduction to transformers", "Difference between encoder, decoder and encoder-decoder architectures", "Attention Mechanisms", "Overview of BERT", "Application of transformers", "Introduction to LARGE LANGUAGE MODELS", "Understanding and handling TEXT DATA", "fine-tuning pre-trained model", "Reward Models and Alignment Strategies", "Practical case studies using SLMs and LLMs", "Deployment of LLMs"]
    }
}

class GeminiFlashcardGenerator:
    def __init__(self, api_key: str = None):
        """Initialize the Gemini API client"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable must be set")
        
        # Initialize the client with the new API
        self.client = genai.Client(api_key=self.api_key)
    
    def generate_flashcards(self, module: str, topic: str = None, count: int = 5, difficulty: str = "medium") -> dict:
        """Generate flashcards for a specific module and topic"""
        
        if module not in SYLLABUS_MODULES:
            raise ValueError(f"Module '{module}' not found in syllabus")
        
        module_info = SYLLABUS_MODULES[module]
        topic_context = f" focusing on {topic}" if topic else ""
        
        prompt = f"""Generate {count} multiple-choice flashcards for {module}{topic_context}.

Difficulty level: {difficulty}
Module context: {', '.join(module_info['topics'][:10])}...

Generate flashcards in this EXACT JSON format (return ONLY pure JSON, no markdown formatting):
{{
  "name": "{module}{' - ' + topic if topic else ''}",
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
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            
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
            
            return {
                'success': True,
                'cards': valid_cards,
                'module': module,
                'topic': topic,
                'deck_name': result.get('name', f"{module}{' - ' + topic if topic else ''}"),
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
