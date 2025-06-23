uv run adk eval src/agents/ src/agents/eval/basic_eval.json --print_detailed_results

# MacroMonger

## To run it locally:
- install uv
-  uv sync
-  uv run adk web
   type: "Fetch news and then analyze each article for market impact"
-  ( new prompt: "Could you please recommend me some financial assets based on the latest news?")

Next Steps
open localhost  http://127.0.0.1:8000/dev-ui/?app=src

## Logic
The **agent team** aimed to do the followings:
- fetch the latest business news from some feeds (yfinance)
- based on the articles it makes sentiment analysis, and categorize the news into
  - news about specific ```asset(s)```
  - news about some asset classes/asset groups/ business areas (```scopes```)
  - ```macro news```
- while processing the news we also build an influence graph, that is, we are searching for keywords(```scopes```), and operational locations, that describes the business of given assets or business areas. Using these we want to propagate impact of more general news (buiness areas and macro) to the tradeable assets.
- when evaluating assets we do the following:
  - we check what ```assets```  were mentioned, with what sentiments specific to each,
  - what asset ```scopes```  have been written about, with what sentiment,
  - what macro news did we find?

We incorporate the freshness of sentiment scores, using an *exponential decay factor*


The sentiment scores of the two latter category (business areas and macro ) are propagated to the individual assets, using the ```location```of operation and the ```scopes```, that describe the assets.

## TODO:
 - go back in time enough - rs index limited aritcle count
 - store the previous articles until their weight does not go to 0
 - work on influences, now only location is used to map influence of macros
