from bs4 import BeautifulSoup
import bs4
import pprint
from os import listdir
from os.path import join
import json
import re

def get_html(dir, warc):

    print("opening ", dir + "/" + warc)
    with open(dir + "/" + warc) as fp:
        lines = fp.readlines()
        response = -1
        http_idx = -1
        for idx, line in enumerate(lines):
            if line.startswith("HTTP"):
                if "200" in line:
                    response = 1
                    http_idx = idx
                else:
                    response = -1
                break 
        #print("response: ", response, "http_idx: ", http_idx)
        html = "" 
        if response == 1:
            url_news = ""
            for i, l in enumerate(lines):
                if l.startswith("WARC-Target-URI"):
                    url_news = l.split()[1]
                if l.startswith("<!DOCTYPE html>"):
                    #print("i: ", lines[i:])
                    html = "\n".join(lines[i:])
                    break
        if html:
            return html, url_news

        
def get_soup(html,url_link):
    # Define final output
    res = dict()
    res["left"], res["right"] = dict(), dict()
    res["left"]["news"] = []
    res["right"]["news"] = []
    res["news_url"] = url_link
    soup = BeautifulSoup(html, 'html.parser')

    # get title
    doc_title = soup.title.string
    doc_title = doc_title.split("|")[0].strip()
    res["title"] = doc_title

    # Get overall intro 
    intro = soup.find("div", "rich-text-block-2 w-richtext") # list of tags find_all?
    if intro == None: return None # if there is no intro, return None
    intro_text = intro.get_text() # [cont.get_text() for cont in intro]
    res["intro"] = intro_text
    # TODO: clean up news sources that appear in intro (e.g. reuters)

    # Get summary 
    left_col = soup.find("div", "column-60 w-clearfix w-col w-col-6 w-col-small-6 w-col-tiny-tiny-stack")
    right_col = soup.find("div", "column-61 w-clearfix w-col w-col-6 w-col-small-6 w-col-tiny-tiny-stack")
    left_in_left_col = left_col.find(text="From the Left")
    right_in_left_col = right_col.find(text="From the Left")
    print("left_in_left_col: ", left_in_left_col)
    print("right_in_left_col: ", right_in_left_col)
    if right_in_left_col == None and left_in_left_col != None: # left is on the left column 
        # Get left summary
        from_the_left = left_col.find("div", "paragraph-6 left intro w-richtext")  #find_all?
    
        # There might not be a summary
        left_intro_text = from_the_left.get_text() if from_the_left else "" #[cont.get_text() for cont in from_the_left]
        if left_intro_text == "": return None
        #print("left intro: ", left_intro_text)
        res["left"]["summary"] = left_intro_text
        
        # Get left news
        # Find first news sources from the left
        def has_sponsored_left(css_class):
            return css_class == "paragraph-6 left bullet first w-richtext" or \
                css_class == "paragraph-6 left bullet first sponsored w-richtext"
        left_news = left_col.find("div", has_sponsored_left) 
        if left_news == None: return None # no news from the left
        #print("left news: ", left_news)
        source = left_news.find("strong")
        #print("source: ", source)
        if source == None: return None

        source = source.get_text() 
        source_len = len(source)

        news_paragraph = left_news.find_all("p") # find_all
        for paragraphs in news_paragraph:
            sub_p = paragraphs.find("a") # if starts with <a>, there should be one and only one url
            if sub_p != None:
                link = sub_p.get('href')

        news_text = left_news.get_text()
        if source_len != 0: # if there is a valid source for this news
            news_text = news_text[:-source_len]
            res["left"]["news"].append({"source": source, "text": news_text, "url": link})


        # If the html page doesn't have this class, then it has all the news in the "paragraph-6 left intro w-richtext"
        # Needs to be treated differently as there are no bars between news - divided by <strong> only 
        # Find all paragraph texts, within them link, followed by <strong>, then move on to the next one  
        left_news_more = left_col.find_all("div", "paragraph-6 left bullet w-richtext")  
        if len(left_news_more) == 0: 
            return None 
            # TODO: find news manually; see above comment 

        
        # The news in left_news_more are divided by bars. 
        # Assume within each bar, there are multiple <p>, one <a>, one <strong>
        for left_more in left_news_more:
            # Get souece
            source = left_more.find("strong")
            print("Source: ", source)
            if source == None: return None
            source = source.get_text() 
            source_len = len(source)
            # Get link
            news_paragraph = left_more.find_all("p") # find_all

      
            for paragraphs in news_paragraph:
                sub_p = paragraphs.find("a") # if starts with <a>, there should be one and only one url
                if sub_p != None:
                    link = sub_p.get('href')

            news_text = left_more.get_text()
            if source_len != 0: # if there is a valid source for this news
                news_text = news_text[:-source_len]
                res["left"]["news"].append({"source": source, "text": news_text, "url": link})
       



        # Get summary for the right
        from_the_right = right_col.find("div", "paragraph-6 right intro w-hidden-tiny w-richtext") 
        # There might not be a summary
        right_intro_text = from_the_right.get_text() if from_the_right else "" 
        if right_intro_text == "": return None
        #print("left intro: ", left_intro_text)
        res["right"]["summary"] = right_intro_text

        def has_sponsored_right(css_class):
            return css_class == "paragraph-6 right bullet first w-richtext" or \
            css_class == "paragraph-6 right bullet first sponsored w-richtext"
                
        right_news = right_col.find("div", has_sponsored_right) 
        if right_news == None: return None # no news from the left
  
        source = right_news.find("strong")
        if source == None: return None

        source = source.get_text() 
        source_len = len(source)

        
        news_paragraph = right_news.find_all("p") # find_all
        for paragraphs in news_paragraph:
            sub_p = paragraphs.find("a") # if starts with <a>, there should be one and only one url
            if sub_p != None:
                link = sub_p.get('href')

        news_text = right_news.get_text()
        if source_len != 0: # if there is a valid source for this news
            news_text = news_text[:-source_len]
            res["right"]["news"].append({"source": source, "text": news_text, "url": link})

        right_news_more = right_col.find_all("div", "paragraph-6 right bullet w-richtext")  
        if len(right_news_more) == 0: 
            return None 
        

        for right_more in right_news_more:
            # Get souece
            source = right_more.find("strong")
            print("Source: ", source)
            if source == None: return None
            source = source.get_text() 
            source_len = len(source)
            # Get link
            news_paragraph = right_more.find_all("p") # find_all

         
            for paragraphs in news_paragraph:
                sub_p = paragraphs.find("a") # if starts with <a>, there should be one and only one url
                if sub_p != None:
                    link = sub_p.get('href')

            news_text = right_more.get_text()
            if source_len != 0: # if there is a valid source for this news
                news_text = news_text[:-source_len]
                res["right"]["news"].append({"source": source, "text": news_text, "url": link})
      
                
        #print("res: ", pprint.pprint(res), "\n\n")
        return res
    
    elif left_in_left_col == None and right_in_left_col != None: # right is on the left column
        print("flipped")
      
        # Right is on the left column. Get summary
        from_the_right = left_col.find("div", "paragraph-6 left intro w-richtext")  #find_all?
    
        # There might not be a summary
        right_intro_text = from_the_right.get_text() if from_the_right else "" #[cont.get_text() for cont in from_the_left]
        if right_intro_text == "": return None
        #print("left intro: ", left_intro_text)
        res["right"]["summary"] = right_intro_text
        #print("summary right: ", right_intro_text )

        def has_sponsored_left(css_class):
            return css_class == "paragraph-6 left bullet first w-richtext" or \
                css_class == "paragraph-6 left bullet first sponsored w-richtext"
        right_news = left_col.find("div", has_sponsored_left) 
        
        if right_news == None: return None # no news from the left
        #print("right news: ", right_news)

        paragraphs = right_news.find_all("p")
        # clea

        # Go through each <p> in paragraphs, add get_text() for that <p> in a list.
        # check if it has <a>. If yes, get link to a list. 
        # check if it has <strong>. If yes, check if has len>1. If yes, time to make an item.
        # Get all text in list, clear the list. 
        # Note <strong> is the last one to appear.

        if len(paragraphs) > 1:
            ps = []
            for p in paragraphs:
                ps.append(p.get_text())

                # check if it has <a>
                a = p.find("a")
                if a != None:
                    link = a.get('href')
                s = p.find("strong")
                if s != None:
                    s = s.get_text()
                    if len(s) > 1:
                        source = s
                        source_len = len(source)
                        # time to assemble a news item
                        assert link != None and len(ps) > 0
                        news_text = (" ".join(ps))[:-source_len]
                        res["right"]["news"].append({"source": source, "text": news_text, "url": link})

                        # empty the list and continue
                        ps = []
                        #print("\n right news: ")
                        #pprint.pprint({"source": source, "text": news_text, "url": link})
            
               
            

        else: #if len(paragraphs) == 1: # all news are written in one single paragraph
  
            print("here. len=1")
            content = paragraphs[0].contents

            # parse line by line
            text = []
            #content = [c for c in content if str(c)!= "<br/>"]
            link = ""
            for c in content:
                #print(type(c),"\n",c, "\n")
                if isinstance(c, bs4.element.NavigableString):
                    text.append(str(c))
                else:
                    t = c.get_text()
                    if len(t) != 0: # if c is not empty <br>
                 
                        if c.name == "a":
                            link = c.get('href')
                            link_text = c.get_text()
                            text.append(link_text)
                   
    
                        if c.name == "strong":
                            source = c.get_text()

                            #print("source: ", source)
                            # make an item
                            if len(text) == 0 or link == "":
                                link = ""
                                text = []
                                continue 
                            assert len(text) > 0 and link != "" # by the time a source is met there must be texts and link found
                            text_joined = " ".join(text)#[:-len_source]
                            res["right"]["news"].append({"source": source, "text": text_joined, "url": link})
                            #print("made an item ", "\n")
                            # pprint.pprint({"source": source, "text": text_joined, "url": link})
                            # print("\n\n")
                            # empty them
                            link = ""
                            text = []
                            
                    

        # Left is on the right column. Get summary
        from_the_left = right_col.find("div", "paragraph-6 right intro w-hidden-tiny w-richtext") 
        # There might not be a summary
        left_intro_text = from_the_left.get_text() if from_the_left else "" #[cont.get_text() for cont in from_the_left]
        if left_intro_text == "": return None
        #print("left intro: ", left_intro_text)
        res["left"]["summary"] = left_intro_text
        # print("summary left: ",left_intro_text )

        def has_sponsored_right(css_class):
            return css_class == "paragraph-6 right bullet first w-richtext" or \
            css_class == "paragraph-6 right bullet first sponsored w-richtext"
      
        left_news = right_col.find("div", has_sponsored_right) 
        if left_news == None: return None # no news from the left
        #print("right news: ", right_news)

        paragraphs = left_news.find_all("p")
        print(len(paragraphs))

        
        if len(paragraphs) > 1:
            ps = []
            for p in paragraphs:
                ps.append(p.get_text())

                # check if it has <a>
                a = p.find("a")
                if a != None:
                    link = a.get('href')
                s = p.find("strong")
                if s != None:
                    s = s.get_text()
                    if len(s) > 1:
                        source = s
                        source_len = len(source)
                        # time to assemble a news item
                        assert link != None and len(ps) > 0
                        news_text = (" ".join(ps))[:-source_len]
                        res["left"]["news"].append({"source": source, "text": news_text, "url": link})

                        # empty the list and continue
                        ps = []
                        print("\n left news: ")
                        pprint.pprint({"source": source, "text": news_text, "url": link})
            
            return res       
        else: 
            print("here. len=1?")
            content = paragraphs[0].contents
            #print(type(content))
            # parse line by line
            text = []
            #content = [c for c in content if str(c)!= "<br/>"]
            link = ""
            for c in content:
                print(type(c),"\n",c, "\n")
                if isinstance(c, bs4.element.NavigableString):
                    text.append(str(c))
                else:
                    t = c.get_text()
                    if len(t) != 0: # if c is not empty <br>
                        print("c: ", type(c), c)
                        print("c name: ", c.name)
                        if c.name == "a":
                            link = c.get('href')
                            link_text = c.get_text()
                            text.append(link_text)
                            print("link: ", link)
                            print("link text: ", link_text)
    
                        if c.name == "strong":
                            source = c.get_text()
                            len_source = len(source)
                            #print("source: ", source)
                            # make an item
                            if len(text) == 0 or link == "":
                                link = ""
                                text = []
                                continue 
                            assert len(text) > 0 and link != "" # by the time a source is met there must be texts and link found
                            text_joined = " ".join(text)#[:-len_source]
                            res["left"]["news"].append({"source": source, "text": text_joined, "url": link})
                            print("made an item ", "\n")
                            # pprint.pprint({"source": source, "text": text_joined, "url": link})
                            # print("\n\n")
                            # empty them
                            link = ""
                            text = []
                            
                    
            return res
        
    else:
        
        return None 




def parse_htmls():
    warcs = [file for file in listdir(DIR_WAR) if not file.startswith('.')]
    parsed_lst = []
    for warc in warcs:
        docs = get_html(DIR_WAR, warc)
        if docs != None:
            soup = get_soup(docs)
            if soup == None: print("no soup!")
            else:
                parsed_lst.append(soup)

    #return
    print("len of the list: ", len(parsed_lst))
    with open(join(DIR_OUTPUT, "parsed" + '.json'), 'w') as f:
        json.dump(parsed_lst, f, indent=4)



##################################

DIR_WAR = "output_warc_35"
DIR_OUTPUT = "output_parsed"

# test1 = "s:--www.theflipside.io-archives-nevada-caucus.warc"
# test1 = "s:--www.theflipside.io-archives-liz-truss.warc"
# test1 = "s:--www.theflipside.io-archives-jan-6-committee.warc"
# test1 = "s:--www.theflipside.io-archives-inflation-6.warc"
#test1 = "s:--www.theflipside.io-archives-border-surge.warc"
#test1 = "s:--www.theflipside.io-archives-minimum-wage.warc"
# warcs = [test1]

if __name__ == "__main__":
    warcs = [file for file in listdir(DIR_WAR) if not file.startswith('.')]
    parsed_lst = []
    for w in warcs: 
        html_link = get_html(DIR_WAR, w)
        if html_link != None: 
            html, url_link = html_link
            res = get_soup(html, url_link)
            if res != None:
                parsed_lst.append(res)

    print("len of the list: ", len(parsed_lst))
    #pprint.pprint(parsed_lst[0])
    with open(join(DIR_OUTPUT, "parsed" + '.json'), 'w') as f:
        json.dump(parsed_lst, f, indent=4)
            
    print("done")

