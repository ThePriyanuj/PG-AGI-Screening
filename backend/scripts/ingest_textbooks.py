"""
[Agent: Data_Architect] — Textbook Ingestion Script
Ingests ML textbooks into ChromaDB with semantic/heading-aware chunking.
Supports: Tom Mitchell's "Machine Learning" & Andriy Burkov's "100-Page ML Book"

Usage:
  python scripts/ingest_textbooks.py --pdf path/to/book.pdf --source "Mitchell ML"
  python scripts/ingest_textbooks.py --sample  (ingest sample ML content)
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_pipeline import ingest_document, get_knowledge_base_stats


SAMPLE_MITCHELL_CONTENT = """
# Chapter 1: Introduction

## 1.1 Well-Posed Learning Problems
A computer program is said to learn from experience E with respect to some class of tasks T and performance measure P, if its performance at tasks in T, as measured by P, improves with experience E.

Machine learning is the study of computer algorithms that improve automatically through experience. It is a subset of artificial intelligence.

## 1.2 Designing a Learning System
The design of a learning system involves several key decisions:
1. Choosing the training experience
2. Choosing the target function
3. Choosing a representation for the target function
4. Choosing a function approximation algorithm

## 1.3 Perspectives and Issues in Machine Learning
Key issues include: What algorithms can approximate functions well? How does the number of training examples influence accuracy? How does the complexity of the hypothesis representation impact learning?

# Chapter 2: Concept Learning and the General-to-Specific Ordering

## 2.1 Introduction to Concept Learning
Concept learning is defined as inferring a boolean-valued function from training examples of its input and output. It can be formulated as a problem of searching through a predefined space of potential hypotheses.

## 2.2 The General-to-Specific Ordering
The general-to-specific ordering provides a useful structure for searching the hypothesis space. Given hypotheses h1 and h2, h1 is more general than h2 if every instance classified positive by h2 is also classified positive by h1.

## 2.3 FIND-S Algorithm
The FIND-S algorithm finds the most specific hypothesis consistent with the training examples. It begins with the most specific hypothesis and generalizes it each time it fails to cover a positive training example.

## 2.4 Candidate Elimination Algorithm
The Candidate Elimination algorithm computes the version space, which is the set of all hypotheses consistent with the training data. It maintains both the most general and most specific boundaries.

# Chapter 3: Decision Tree Learning

## 3.1 Introduction to Decision Trees
Decision tree learning is a method for approximating discrete-valued target functions. The learned function is represented as a decision tree, which classifies instances by sorting them from the root to some leaf node.

## 3.2 ID3 Algorithm
The ID3 algorithm builds decision trees using a top-down, greedy approach. At each node, it selects the attribute that best classifies the local training examples using information gain.

Information Gain measures the expected reduction in entropy caused by partitioning the examples according to an attribute.

## 3.3 Entropy and Information Gain
Entropy is a measure of the impurity or randomness in a set. For a collection S containing positive and negative examples:
Entropy(S) = -p_positive * log2(p_positive) - p_negative * log2(p_negative)

## 3.4 Overfitting in Decision Trees
A hypothesis overfits the training data if there exists some alternative hypothesis that has a larger error on the training data but a smaller error on the entire distribution of instances. Pruning methods help address overfitting.

# Chapter 4: Artificial Neural Networks

## 4.1 Introduction to Neural Networks
Artificial neural networks provide a general, practical method for learning real-valued, discrete-valued, and vector-valued functions from examples. They are inspired by biological neural networks.

## 4.2 Perceptrons
A perceptron takes a vector of real-valued inputs, calculates a linear combination of these inputs, then outputs 1 if the result is greater than some threshold and -1 otherwise.

## 4.3 Gradient Descent and the Delta Rule
The delta rule uses gradient descent to minimize the squared error between the target output and the actual output. The weight update rule is: w_i = w_i + eta * (t - o) * x_i

## 4.4 Backpropagation Algorithm
Backpropagation learns the weights for a multilayer network by propagating errors backward from the output layer. It uses the chain rule of calculus to compute the gradient of the error with respect to each weight.

## 4.5 Overfitting in Neural Networks
Neural networks are prone to overfitting, especially with many hidden units. Regularization techniques like weight decay, early stopping, and dropout help mitigate this.

# Chapter 5: Evaluating Hypotheses

## 5.1 Estimating Hypothesis Accuracy
The true error of a hypothesis is the probability that it will misclassify a single randomly drawn instance. The sample error is the fraction of misclassifications on a sample.

## 5.2 Cross-Validation
K-fold cross-validation partitions the data into k subsets. Each subset is used once as the test set while the remaining k-1 subsets form the training set. This provides a more reliable estimate of performance.

## 5.3 Bias and Variance
The bias-variance decomposition shows that the expected error of a learning algorithm can be decomposed into bias (systematic error) and variance (sensitivity to training data). Understanding this tradeoff is crucial.

# Chapter 6: Bayesian Learning

## 6.1 Bayes Theorem
Bayes theorem provides a principled way to calculate the posterior probability of a hypothesis given the data: P(h|D) = P(D|h) * P(h) / P(D)

## 6.2 Maximum A Posteriori Hypothesis
The MAP hypothesis is the one that maximizes the posterior probability. When all hypotheses are equally probable a priori, MAP reduces to Maximum Likelihood.

## 6.3 Naive Bayes Classifier
The Naive Bayes classifier assumes that attribute values are conditionally independent given the target value. Despite this simplifying assumption, it performs well in many practical applications.

# Chapter 7: Computational Learning Theory

## 7.1 PAC Learning
The Probably Approximately Correct (PAC) learning framework characterizes the number of training examples needed to learn a concept. A concept class is PAC-learnable if a polynomial number of examples suffices.

## 7.2 Sample Complexity
Sample complexity refers to the number of training examples needed to learn a target concept within specified bounds of accuracy and confidence. It grows with the complexity of the hypothesis space.

# Chapter 8: Instance-Based Learning

## 8.1 K-Nearest Neighbors
The k-nearest neighbors algorithm classifies new instances by finding the k most similar training instances and using their labels to predict. Distance metrics like Euclidean distance are commonly used.

## 8.2 Locally Weighted Regression
Locally weighted regression constructs an approximation to the target function in the neighborhood of each query point, weighting training examples by their distance to the query.

# Chapter 9: Support Vector Machines

## 9.1 Maximum Margin Classifier
Support vector machines find the hyperplane that maximizes the margin between classes. The margin is the distance between the decision boundary and the nearest data points (support vectors).

## 9.2 Kernel Functions
Kernel functions allow SVMs to operate in high-dimensional feature spaces without explicitly computing the coordinates. Common kernels include linear, polynomial, and radial basis function (RBF).

# Chapter 10: Ensemble Methods

## 10.1 Bagging
Bootstrap aggregating (bagging) trains multiple models on random subsets of the training data and combines their predictions through voting or averaging. Random forests extend bagging to decision trees.

## 10.2 Boosting
Boosting algorithms like AdaBoost train a sequence of weak learners, each focusing on the examples that previous learners misclassified. The final prediction is a weighted vote of all learners.
"""

SAMPLE_BURKOV_CONTENT = """
# Chapter 1: Introduction

## What is Machine Learning
Machine learning is a subfield of computer science that is concerned with building algorithms which, to be useful, rely on a collection of examples of some phenomenon. These examples can come from nature, be handcrafted by humans, or generated by another algorithm.

## Types of Learning
Supervised learning: The dataset is a collection of labeled examples. Each example is a feature vector paired with a label. The goal is to produce a model that takes a feature vector as input and outputs a prediction.

Unsupervised learning: The dataset is a collection of unlabeled examples. The goal is to find patterns, structure, or knowledge in the data without using labels.

## When to Use Machine Learning
Machine learning is best suited for problems where: the patterns are complex and cannot be manually programmed, the data changes frequently, and the task requires personalization.

# Chapter 2: Notation and Definitions

## Feature Vectors
A feature vector is an ordered list of numerical properties of an observed phenomenon. Each feature measures some property of the phenomenon.

## Model and Loss Function
A model is a mathematical function that maps feature vectors to predictions. The loss function measures how well the model performs.

# Chapter 3: Fundamental Algorithms

## Linear Regression
Linear regression models the relationship between input features and a continuous output variable as a linear function. The parameters are learned by minimizing the mean squared error.

## Logistic Regression
Logistic regression is used for binary classification. It models the probability of the positive class using the sigmoid function applied to a linear combination of features.

## Decision Trees
A decision tree is a flowchart-like structure where each internal node tests a feature, each branch corresponds to a test outcome, and each leaf assigns a class label.

## Support Vector Machines
SVMs find the optimal hyperplane that separates classes with the maximum margin. For non-linearly separable data, kernel tricks map data into higher-dimensional spaces.

## k-Nearest Neighbors
KNN classifies a new example by finding the k closest training examples in the feature space and assigning the majority class among them.

# Chapter 4: Anatomy of a Learning Algorithm

## Gradient Descent
Gradient descent is an optimization algorithm used to minimize the loss function. It iteratively adjusts parameters in the direction of the negative gradient.

## Stochastic Gradient Descent
SGD updates parameters using one randomly chosen example at a time, making it faster for large datasets but noisier.

## Learning Rate
The learning rate controls the step size during optimization. Too large a learning rate causes divergence; too small leads to slow convergence.

# Chapter 5: Basic Practice

## Feature Engineering
Feature engineering involves creating new features from existing ones to improve model performance. Good features capture the underlying patterns in the data.

## Regularization
Regularization adds a penalty term to the loss function to prevent overfitting. L1 regularization encourages sparsity; L2 regularization penalizes large weights.

## Cross-Validation
Cross-validation estimates model performance by training and testing on different subsets of the data. Common approaches include k-fold and leave-one-out.

## Bias-Variance Tradeoff
High bias (underfitting): model is too simple. High variance (overfitting): model is too complex. The goal is to find the right balance.

# Chapter 6: Neural Networks and Deep Learning

## Feed-Forward Neural Networks
A feed-forward neural network consists of layers of neurons. Each neuron computes a weighted sum of inputs, applies an activation function, and passes the result to the next layer.

## Backpropagation
Backpropagation computes gradients of the loss function with respect to each weight by applying the chain rule backwards through the network.

## Convolutional Neural Networks
CNNs use convolutional layers to detect local patterns in spatial data (like images). Key components include filters, pooling layers, and feature maps.

## Recurrent Neural Networks
RNNs process sequential data by maintaining a hidden state that captures information from previous time steps. LSTMs and GRUs address the vanishing gradient problem.

# Chapter 7: Problems and Solutions

## Overfitting
Solutions: more training data, regularization, dropout, early stopping, ensemble methods.

## Imbalanced Classes
Solutions: oversampling minority class, undersampling majority class, cost-sensitive learning, synthetic data generation (SMOTE).

## Feature Selection
Methods: mutual information, chi-squared test, recursive feature elimination, L1 regularization.

# Chapter 8: Advanced Practice

## Transfer Learning
Transfer learning uses a model trained on one task as the starting point for a model on a different but related task. Fine-tuning adjusts the pre-trained model to the new task.

## Ensemble Learning
Combining multiple models often yields better performance than any single model. Methods include bagging, boosting, and stacking.

## Dimensionality Reduction
PCA and t-SNE reduce the number of features while preserving important information. This helps with visualization and can improve model performance.
"""


def main():
    parser = argparse.ArgumentParser(description="Ingest textbooks into PG-AGI knowledge base")
    parser.add_argument("--pdf", type=str, help="Path to PDF textbook")
    parser.add_argument("--source", type=str, default="Unknown", help="Source book name")
    parser.add_argument("--sample", action="store_true", help="Ingest sample ML content")
    
    args = parser.parse_args()
    
    if args.sample:
        print("Ingesting sample Mitchell ML content...")
        count1 = ingest_document(SAMPLE_MITCHELL_CONTENT, "Tom Mitchell - Machine Learning")
        print(f"  Ingested {count1} chunks from Mitchell")
        
        print("Ingesting sample Burkov 100-Page ML content...")
        count2 = ingest_document(SAMPLE_BURKOV_CONTENT, "Andriy Burkov - The Hundred-Page Machine Learning Book")
        print(f"  Ingested {count2} chunks from Burkov")
        
        stats = get_knowledge_base_stats()
        print(f"\nKnowledge Base Stats: {stats}")
        return
    
    if args.pdf:
        import PyPDF2
        import io
        
        print(f"Reading PDF: {args.pdf}")
        with open(args.pdf, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        print(f"Extracted {len(text)} characters")
        count = ingest_document(text, args.source)
        print(f"Ingested {count} chunks from '{args.source}'")
        
        stats = get_knowledge_base_stats()
        print(f"Knowledge Base Stats: {stats}")
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
