import pymongo as mongo

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

import nltk
from nltk.corpus import stopwords
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

options = Options()
service = Service("chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

# def make_prediction():
#     pass

def create_con(b_list):
    try:
        client = mongo.MongoClient("mongodb://localhost:27017/")
        if "amzn_db" not in client.list_database_names():
            db = client["amzn_db"]
            amzn_books = db["amzn_books"]
            amzn_books.insert_many(b_list)
        else:
            if client.get_database("amzn_db").get_collection("amzn_books") != "":
                amzn_books = client.get_database("amzn_db").get_collection("amzn_books")
                amzn_books.delete_many({})
                amzn_books.insert_many(b_list)
            else:
                client.get_database("amzn_db").create_collection(
                    "amzn_books").insert_many(b_list)
    except Exception as E:
        raise E
        print("Error occur red!", E)
    finally:
        client.close()

def get_comment(url):
    get_url(url)
    country = driver.find_elements(By.XPATH, "//span[@class='a-size-base a-color-secondary review-date']")
    comments = driver.find_elements(By.XPATH, "//div[@class='a-expander-content "
                                              "reviewText review-text-content "
                                              "a-expander-partial-collapse-content']")
    country = [i.text for i in country]
    comments = [i.text for i in comments]

    for i in range(len(country)-1, -1, -1):
        if country[i].lower().split()[0] != "türkiye’de":
            comments.pop(i)
    return comments

def nlp_comment(comment):
    t_stopwords = stopwords.words("turkish")
    if comment not in ["", None]:
        tokens = nltk.word_tokenize(comment, language="turkish")
        tokens = [i.lower() if i.isalnum() and i not in t_stopwords else tokens.pop(
            tokens.index(i))
                  for i in tokens]
    return tokens

def nlp_sentiment(comment, s_pipeline):
    sentiment = s_pipeline(comment)
    return sentiment

def get_url(url):
    try:
        driver.get(url)
    except:
        return -1

def print_console():
    model = AutoModelForSequenceClassification.from_pretrained(
        "savasy/bert-base-turkish-sentiment-cased")
    tokenizer = AutoTokenizer.from_pretrained("savasy/bert-base-turkish-sentiment-cased")
    sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

    x = get_comment(
        "https://www.amazon.com.tr/Rezonans-Kanunu-Pierre-Franckh/dp/6057572181/ref=sr_1_1?dib=eyJ2IjoiMSJ9.ojn3-kQM-Ug9gIraUAWpi_hJXV6rQyKjRgzuCGO4NIXeEJ0crzeH2Ko9bQwkDPSmKSGkMpDEnJ6RuFv7PkO225z01C1V_iPFXg1ADJIcct769LA5EzF3KNeW1kFPGmEuktIBYwWn9U5xu_xlMsO50Ef9BC02nWNpxFhcg9UuOlLlgat3PsPKZJGJKp5CkZLu5MCvSiOKjxtIjLLTCs7ri4RVH-JgH9MlaMs9ywWaf0A.nHLIa0SnRXNFYGlT8GK7Uo3F3jtLtnGEPzYbsUoZe8A&dib_tag=se&qid=1727849049&refinements=p_85%3A21345931031%2Cp_n_format_browse-bin%3A13815617031&rps=1&s=books&sr=1-1")
    i = 0
    while i < len(x):
        print("Comment:", x[i], "| Score:", nlp_sentiment(x[i], sentiment_pipeline))
        i += 1

def get_data():
  name = driver.find_elements(By.XPATH, "//span[@class='a-size-medium a-color-base a-text-normal']")
  price = driver.find_elements(By.XPATH, "//span[@class='a-price']")
  order_num = driver.find_elements(By.XPATH, "//span[@class='a-size-base s-underline-text']")
  rating = driver.find_elements(By.XPATH, "//span[@class='a-icon-alt']")
  return name, price, order_num, rating

def main():
    get_url(f"https://www.amazon.com.tr/s?i=stripbooks&bbn=27913399031&rh=n%3A27913399031%2Cp_85%3A21345931031%2Cp_n_format_browse-bin%3A13815617031&dc&page={1}&pf_rd_i=12466380031&pf_rd_m=A1UNQM1SR2CHM&pf_rd_p=918eab22-c173-4cec-a9d0-1ee778272a73&pf_rd_r=GKRR1QG6EBSESYZZD2C0&pf_rd_s=merchandised-search-4&pf_rd_t=101&qid=1727691525&rnid=13815614031&ref=sr_pg_{1}")

    driver.maximize_window()

    name, price, order_num, rating = get_data()
    books = list()

    for i in range(len(name)):
      temp_dict = {}
      temp_dict["Name"] = name[i].text
      temp_dict["Price (TL)"] = float(price[i].text.replace("\n",".").replace("TL",""))
      temp_dict["Order Quantity"] = int(order_num[i].text.replace(".",""))
      temp_dict["Rating (5)"] = float(rating[i].get_attribute("textContent").split(" ")[-1].replace(",","."))
      books.append(temp_dict)

    print_console()
    create_con(books)

if __name__ == "__main__":
    main()