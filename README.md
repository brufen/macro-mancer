# Macro-Mancer: Financial AI Agent System

## Overview
**Macro-Mancer** is a sophisticated financial AI system that analyzes macroeconomic news and provides asset recommendations using Google's Agent Development Kit (ADK). It combines news scraping, sentiment analysis, and machine learning to identify market opportunities.

🤖 Agent Pipeline

| Agent           | Purpose  |
|-----------------|---|
| news_fetcher    | Scrape RSS feeds	  |
| news_analyzer   | Sentiment analysis	 |
| db_saver        | Persist data	  |
| recommender     |  Generate recs	 |


## 🧐 Logic
The **Agent sequential team** aimed to do the followings:
- Fetch the latest business news from some feeds (used source: Yahoo Finance)
- Based on the articles it makes sentiment analysis, and categorize the 
  news into
   - news about specific ```asset(s)```
   - news about some asset classes/asset groups/ business areas (```scopes```)
   - ```macro news```
- While processing the news we also build an influence graph, that is, we 
  are searching for keywords(```scopes```), and operational locations, that describes the business of given assets or business areas. Using these we want to propagate impact of more general news (buiness areas and macro) to the tradeable assets.
- When evaluating assets we do the following:
   - we check what ```assets```  were mentioned, with what sentiments specific to each,
   - what asset ```scopes```  have been written about, with what sentiment,
   - what macro news did we find?

- We incorporate the freshness of sentiment scores, using an *exponential 
decay factor*.


- The sentiment scores of the two latter category (business areas and macro )
are propagated to the individual assets, using the ```location```of operation and the ```scopes```, that describe the assets.


🚀 Usage Examples

**Basic Recommendation Request**

"Can you recommend me some financial assets based on the latest news?"


## Key Features 
### Intelligent Analysis
   - Multi-dimensional Impact: Analyzes assets, sectors, and macro events
   - Geographic Awareness: Tracks regional economic impacts 
   - Temporal Weighting: Recent news weighted higher than older news 
   - Confidence Scoring: Impact scores with validation

### Scalable Design
   - Microservices Ready: Each agent is independent
   - Configurable Sources: Easy to add new RSS feeds, Model, DB or Memory use.
   - Environment Agnostic: Works locally and in GCP
   - Testable: Clear interfaces for unit testing
   
### 🛠️ Technical Stack
* AI Framework: Google Agent Development Kit (ADK) 
* Language Model: Gemini 2.0 Flash Exp
* Database: PostgreSQL on Google Cloud SQL
* ORM: SQLAlchemy with async support
* Validation: Pydantic models
* Infrastructure: Terraform for GCP provisioning
* Package Management: uv (Python)
* Architecture: Hexagonal (Ports & Adapters)


### 📈 Business Value
* Real-time Market Intelligence: Automated news analysis
* Quantified Sentiment: Numerical impact scores for decision making
* Historical Context: Combines current and past analyses
* Auditable Pipeline: Full traceability of recommendations


### 🎯 Current Capabilities
* News Scraping: RSS feeds with professional headers
* Sentiment Analysis: Multi-dimensional impact scoring
* Database Integration: Persistent storage with SQLAlchemy
* Asset Recommendations: Weighted scoring algorithm
* Hexagonal Architecture: Clean, maintainable codebase
* Logging & Monitoring: Comprehensive error tracking
* GCP Integration: Terraform infrastructure as code


### 🌟 Future Development Roadmap
- More configurable RSS feed source
- Historical Data updates (store the previous articles until their weight 
  don't reach 0)
- Model Training: ML model refinement using past data
- API Development (Production Ready)
  - REST API: Standard HTTP endpoints for trading platforms
  - gRPC API: High-performance streaming for real-time data 
- Authentication: API key management and rate limiting
- Trading Platform Integration
   -  AlgoTrading Support: Direct integration with trading systems
- Risk Management: Position sizing and stop-loss suggestions




### Architecure: 



