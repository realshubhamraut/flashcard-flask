"""
AI-powered flashcard generation using Google Gemini API
"""
import os
import json
from google import genai
from google.genai import types
from typing import List, Dict, Optional

# Syllabus modules mapping
SYLLABUS_MODULES = {
    "Linux Programming and Cloud Computing": {
        "hours": 50,
        "topics": [
            "Linux Installation (Ubuntu and CentOS)",
            "Basics of Linux, Configuring Linux, Shells, Commands, and Navigation",
            "Common Text Editors",
            "Administering Linux",
            "Introduction to Users and Groups",
            "Linux shell scripting, shell computing",
            "Introduction to enterprise computing, Remote access",
            "Introduction to Git/GitHub/Gitlab",
            "Version control systems",
            "Creating GitHub repository",
            "Git commands and project management",
            "Cloud Computing Basics",
            "Cloud Vendors (AWS: EC2, Lambda; Azure: Virtual Machines, Data Factory)",
            "SAAS, PAAS, IAAS",
            "Cloud deployment and applications"
        ]
    },
    "Python and R Programming": {
        "hours": 80,
        "topics": [
            "Python basics, Control Structures",
            "If-else, Looping (For, While, Nested loops)",
            "Break, Continue, Pass",
            "Strings and Tuples",
            "Lists, Functions and Methods",
            "Files, Pickling, Modules",
            "Dictionaries, Dictionary Comprehension",
            "Functions and Functional Programming",
            "Visualization (Matplotlib, Seaborn)",
            "OOPs concept, Class and object, Inheritance",
            "Overloading, Overriding, Data hiding",
            "Generators, Decorators",
            "Exception Handling",
            "Data wrangling, Data cleaning",
            "Python libraries (pillow, scikit-learn)",
            "Python virtual environment, Logging",
            "R Programming basics",
            "Data Objects in R",
            "Manipulating and Processing Data in R",
            "Control Structures, Functions in R",
            "R Packages (Tidyverse, Dplyr, Tidyr)",
            "Queuing Theory"
        ]
    },
    "Java Programming": {
        "hours": 70,
        "topics": [
            "Java Virtual Machine",
            "Data Types, Operators",
            "OOPs Concepts",
            "Inner Classes and Inheritance",
            "Interface and Package",
            "Exceptions",
            "Collections",
            "Threads",
            "Java.lang, Java.util",
            "Lambda Expressions",
            "Streams",
            "JDBC API"
        ]
    },
    "Advanced Analytics using Statistics": {
        "hours": 90,
        "topics": [
            "Business Analytics case studies",
            "Summary Statistics, Descriptive Statistics",
            "Probability theory",
            "Probability Distributions (Normal, Binomial, Poisson)",
            "Sampling and Estimation",
            "Bayes' Theorem, Central Limit theorem",
            "Hypothesis Testing",
            "Parametric Tests: ANOVA, t-test",
            "Non-parametric Tests: chi-Square, U-Test",
            "Correlation, Covariance, Outliers",
            "Simulation and Risk Analysis",
            "Optimization, Linear, Integer",
            "Factor Analysis",
            "Predictive Modelling",
            "Decision Analytics",
            "Evidence and Probabilities",
            "Business Strategy",
            "Python Libraries (Pandas, Numpy, Scrapy, Plotly, Beautiful soup)"
        ]
    },
    "Data Collection and DBMS": {
        "hours": 90,
        "topics": [
            "Database Concepts (File System and DBMS)",
            "OLAP vs OLTP",
            "Database Storage Structures",
            "Structured and Unstructured data",
            "SQL Commands (DDL, DML, DCL)",
            "Stored functions and procedures",
            "Conditional Constructs in SQL",
            "Database schema design",
            "Normal Forms and ER Diagram",
            "Relational Database modelling",
            "Triggers",
            "Data Warehousing",
            "No-SQL",
            "XML, MongoDB, Cassandra",
            "Connecting DB's with Python",
            "Data Lakes concepts and architecture",
            "Data Lake vs Data Warehouse vs Lakehouse",
            "Delta Lake with analytics and AI"
        ]
    },
    "Big Data Technologies": {
        "hours": 150,
        "topics": [
            "Big Data Introduction",
            "Hadoop ecosystem and stack",
            "HDFS (Hadoop Distributed File System)",
            "MapReduce",
            "Hadoop cluster setup",
            "Security in Hadoop",
            "Apache Airflow/ETL Informatica",
            "Data warehousing for ETL",
            "ETL vs ELT",
            "HIVE programming",
            "HBase overview and operations",
            "Apache Spark overview",
            "Resilient Distributed Datasets (RDDs)",
            "PySpark",
            "Spark Streaming",
            "Spark MLlib and ML APIs",
            "Spark SQL, Spark Data Frames",
            "Integration of Spark and Kafka",
            "Kafka Producer and Consumer",
            "Map Reduce"
        ]
    },
    "Data Visualization": {
        "hours": 50,
        "topics": [
            "Business Intelligence requirements",
            "Information Visualization",
            "Data analytics Life Cycle",
            "Analysis vs. Reporting",
            "MS Excel: Functions, Formula, charts, Pivots, Lookups",
            "Data Analysis Tool pack",
            "Introduction to Tableau",
            "Data sources in Tableau",
            "Taxonomy of data visualization",
            "Calculations in Tableau",
            "LOD (Level of Detail) Expressions",
            "Modern Data Analytic Tools",
            "Visualization Techniques"
        ]
    },
    "Practical Machine Learning": {
        "hours": 140,
        "topics": [
            "Introduction to machine learning",
            "PAC learning, Bias complexity trade off",
            "VC Dimension",
            "Regularization and Stability",
            "Model Selection and Validation",
            "Supervised, Unsupervised, Semi-supervised Learning",
            "Clustering (K-Means, Hierarchical)",
            "Dimension Reduction (PCA, Kernel PCA, LDA)",
            "Information theory fundamentals",
            "Classification and Regression (KNN, Decision Trees)",
            "Bayesian analysis and Naïve Bayes",
            "Random forest, Gradient boosting",
            "SVM, XGBoost, CatBoost",
            "Linear and Non-linear regression",
            "Time series Forecasting",
            "Neural networks (Neurons, backpropagation)",
            "Deep Feedforward Networks",
            "Convolutional Neural Networks",
            "Recurrent Neural Networks",
            "Transfer Learning, Autoencoders",
            "Object Detection, Segmentation, Tracking",
            "NLP concepts",
            "Transformers (encoder, decoder architectures)",
            "Attention Mechanisms, BERT",
            "Large Language Models (LLMs)",
            "Fine-tuning pre-trained models",
            "Reward Models and Alignment",
            "Deployment of LLMs"
        ]
    }
}


class GeminiFlashcardGenerator:
    """Generate flashcards using Google Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini API
        Args:
            api_key: Google Gemini API key (if None, reads from GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        # Initialize the new Gemini client
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = 'gemini-1.5-flash'
    
    def generate_flashcards(
        self, 
        module_name: str, 
        topic: Optional[str] = None,
        count: int = 50,
        difficulty: str = "medium"
    ) -> List[Dict]:
        """
        Generate flashcards for a specific module and topic
        
        Args:
            module_name: Name of the syllabus module
            topic: Specific topic within module (if None, covers all topics)
            count: Number of flashcards to generate
            difficulty: Difficulty level (easy, medium, hard)
        
        Returns:
            List of flashcard dictionaries
        """
        if module_name not in SYLLABUS_MODULES:
            raise ValueError(f"Module '{module_name}' not found in syllabus")
        
        module_info = SYLLABUS_MODULES[module_name]
        topics_list = module_info['topics']
        
        # Build topic context
        if topic:
            topic_context = f"Focus specifically on: {topic}"
        else:
            topic_context = f"Cover all topics in the module: {', '.join(topics_list)}"
        
        prompt = self._build_prompt(module_name, topic_context, count, difficulty)
        
        try:
            # Use the new client API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            flashcards = self._parse_response(response.text)
            return flashcards[:count]  # Ensure we don't exceed requested count
        except Exception as e:
            raise Exception(f"Failed to generate flashcards: {str(e)}")
    
    def _build_prompt(self, module_name: str, topic_context: str, count: int, difficulty: str) -> str:
        """Build the prompt for Gemini API"""
        return f"""You are an expert educator creating high-quality flashcards for a Data Science and AI curriculum.

MODULE: {module_name}
TOPIC CONTEXT: {topic_context}
COUNT: {count} flashcards
DIFFICULTY: {difficulty}

Generate exactly {count} high-quality multiple-choice flashcards in JSON format.

REQUIREMENTS:
1. Each flashcard must have:
   - question_text: Clear, concise question
   - options: Dictionary with keys a, b, c, d (4 options)
   - correct_answer: Letter of correct option (a, b, c, or d)
   - explanation: Detailed explanation of why the answer is correct
   - difficulty: {difficulty}
   - code_blocks: Array of code examples (if applicable, otherwise empty array)

2. Question types to include:
   - Conceptual understanding (30%)
   - Practical application (40%)
   - Code-based questions (20%)
   - Best practices and troubleshooting (10%)

3. Quality standards:
   - Questions should be clear and unambiguous
   - All options should be plausible
   - Explanations should be educational and detailed
   - Include code examples where relevant
   - Cover different aspects of the topic
   - Avoid trivial or overly simple questions

4. For code-based questions:
   - Use realistic, practical code examples
   - Include proper syntax
   - Focus on common patterns and pitfalls

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question_text": "What is the primary purpose of HDFS in Hadoop?",
    "options": {{
      "a": "To process data in parallel",
      "b": "To store large datasets across distributed nodes",
      "c": "To manage user authentication",
      "d": "To schedule MapReduce jobs"
    }},
    "correct_answer": "b",
    "explanation": "HDFS (Hadoop Distributed File System) is designed to store very large datasets reliably across distributed nodes in a Hadoop cluster. It provides high-throughput access to application data and is fault-tolerant through data replication.",
    "difficulty": "{difficulty}",
    "code_blocks": []
  }}
]

Generate exactly {count} flashcards now. Return ONLY the JSON array, no other text."""

    def _parse_response(self, response_text: str) -> List[Dict]:
        """Parse Gemini response and extract flashcards"""
        try:
            # Remove markdown code blocks if present
            clean_text = response_text.strip()
            if clean_text.startswith('```json'):
                clean_text = clean_text[7:]
            if clean_text.startswith('```'):
                clean_text = clean_text[3:]
            if clean_text.endswith('```'):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            # Parse JSON
            flashcards = json.loads(clean_text)
            
            if not isinstance(flashcards, list):
                raise ValueError("Response is not a JSON array")
            
            # Validate structure
            validated_cards = []
            for card in flashcards:
                if self._validate_card(card):
                    validated_cards.append(card)
            
            return validated_cards
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {str(e)}\nResponse: {response_text[:500]}")
    
    def _validate_card(self, card: Dict) -> bool:
        """Validate flashcard structure"""
        required_fields = ['question_text', 'options', 'correct_answer', 'explanation', 'difficulty']
        
        # Check required fields
        if not all(field in card for field in required_fields):
            return False
        
        # Validate options
        if not isinstance(card['options'], dict):
            return False
        
        # Must have at least 2 options
        if len(card['options']) < 2:
            return False
        
        # Correct answer must be a valid option key
        if card['correct_answer'] not in card['options']:
            return False
        
        return True


def get_available_modules() -> Dict[str, Dict]:
    """Get all available syllabus modules"""
    return SYLLABUS_MODULES


def get_module_topics(module_name: str) -> List[str]:
    """Get topics for a specific module"""
    if module_name in SYLLABUS_MODULES:
        return SYLLABUS_MODULES[module_name]['topics']
    return []
