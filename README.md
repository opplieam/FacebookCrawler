# Facebook page crawler
Facebook page crawler is a web spider for facebook, written in [Scrapy](https://scrapy.org/) framework Currently, 
support only Facebook Page. Given a page id, It can extract all the posts, images url, reaction count, comment count 
and so on.

This project is the new version of [this repo](https://github.com/opplieam/Facebook_page_crawler)

## DISCLAIMER
This script is not authorized by Facebook. For commercial used please contact [Facebook](https://facebook.comorg/).

The purpose of this script is for **educational**, to demonstrate how Scrapy can be written to extract page with less 
help of headless browser.

Use it at your own risk.

## WARNING
Your facebook account might get suspend if your spider run very fast. Please careful.

Try to increase download_delay in `settings.py`

## Installation

It's recommended to install inside an isolate environment. In this case, I had provided `requirement.text` 
that can be used by `pip`

`python3.10`
`pip install -r requirements.txt`

You also need `docker` to run headless browser service like splash.

## Data schema

```
{
    page_id
    page_name
    page_url
    post_id
    post_url
    post_text
    image_urls
    comment_count
    reaction_count
    share_count
    comments: [
        comment_id
        comment_text
        comment_reaction_count
        author_url
        author_name
    ]
}
```

## Usage

Run splash with docker at port :8050

`docker run -p 8050:8050 scrapinghub/splash`

In `settings.py` please add `SPLASH_URL = 'http://localhost:8050`
It should already be provided in the project.


You can access UI splash via `http://localhost:8050`

In order to run the spider, you need to provide some arguments.

Arguments lists

`-a email=your_email@gmail.com` required

`-a password=strongpassword` required

`-a page_id=ejeab` required | or multiple pages split by `,` `-a page_id=ejeab,victiousant`

`-a limit=-1` optional. the limit items will be scraped, `-1` unlimited, default is `100`

`-o output.json` output the file with json format

Example to run spider and store data as `fb.json`

```
scrapy crawl fb_page \ 
-a email="myemail@hotmail.com" \ 
-a password="strongpass" \ 
-a page_id="ejeab" \ 
-a limit=-1 \ 
-o fb.json
```

## Why splash

Currently, facebook using a client side encryption password before sending to server.
Instead of sending a plaintext password

`strongpass` it's got encrypted like this
`#PWD_BROWSER:5:........`

It would be tedious to reverse engineer and try to get it right. So I use a `splash` for login request grab a cookies and 
the rest is just normal scrapy parsing

Splash is lightweight headless browser which run as a separate service. So it's ready to scale when you have to develop 
a large scale web crawling system. You can use something like Selenium or Playwright, but it is memory hog. it can be 
expensive in a long run when running in cloud.

## How about database

The recommend way to store data into database is, storing after the spider done the job. or when the spider is 
in a close signal state. Ideally the step should be like this

```
- Spider crawl data and store result as output.json file
- After spider done a jobs. Download or open file
- Crawl all data into database
Please see `middlewares.py`:22 as example
```

Scraping is already an IO bound task. If you inject another IO bound task like writing to a database. It's not going 
to scale well in the large scale crawling system.

Also, Most database doesn't optimize for writing a query. Unless you are using a `CQRS pattern` Then it's ok to inject
the database call.

## Thing that can be improved

As this project is for educational, it does not a complete feature.
```
- Support nested comments parsing
- Get pagination call for comments
- Avoid banning issue ?
```
