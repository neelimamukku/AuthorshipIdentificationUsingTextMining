# -*- coding: utf-8 -*-
"""AuthorshipIdentification.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11iEXyWDrV5QKimGcESPOS9HIJw8eNEIU
"""

import os
from glob import glob
import zipfile
import chardet
from collections import Counter
from bs4 import BeautifulSoup
import pandas as pd
import random
import re
from typing import List
import pathlib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

zipfile.ZipFile("/content/drive/MyDrive/Authorship_Identification/blogs.zip").extractall()

blogs_ds = "/content/blogs"

def get_all_xml_files_in_folder(blogs_ds):
  return glob(os.path.join(blogs_ds, "*.xml")) 
def load_file(filename):
  with open(filename, 'rb') as inf:
    return inf.read()

filenames = get_all_xml_files_in_folder(blogs_ds)
filename = filenames[0]
contents = load_file(filename)

print(filename)
print(contents)
print(type(contents))
chardet.detect(contents)

limit = 30

encodings = {}
for filename in filenames:
  encodings[filename] = chardet.detect(load_file(filename))
  if limit and len(encodings) >= limit:
    break
most_likely_encodings = {filename: encoding['encoding'] for filename, encoding in encodings.items()}
frequencies = Counter(most_likely_encodings.values())
frequencies.most_common(20)

def extract_posts(filename):
  contents = load_file(filename)
  soup = BeautifulSoup(contents, 'xml')
  posts = [p.contents[0] for p in soup.find_all('post') if len(p.contents)]
  return posts

posts = []
number_read = 0
for filename in filenames:
  try:
    number_read += 1
    if number_read > limit:
      break
    posts = posts + extract_posts(filename)
  except Exception as e:
    print("Error with file: ",{filename})
    raise e
print(posts[0][:50],len(posts))

remove_urlLink_match = re.compile("urlLink")
def postprocess(document):
  document = remove_urlLink_match.sub("", document)
  document = document.strip()
  return document

class Post:
  author_number: int
  gender: str
  age: int
  industry: str
  star_sign: str
  #date: str
  post: str
  def to_dict(self):
    return {key: getattr(self, key) for key in ['author_number', 'gender', 'age', 'industry', 'star_sign', 'post']}
  def load_from_file(filename):
    age, author_number, gender, industry, star_sign = Post.extract_attributes_from_filename(filename)
    with open(filename, 'rb') as inf:
      contents = load_file(filename)
      #print(type(contents))
      soup = BeautifulSoup(contents, 'xml')
      posts = [Post.create_from_attributes(author_number, gender, age, industry, star_sign,postprocess(p.contents[0])) for p in soup.find_all('post') if len(p.contents)]
    return posts
  def extract_attributes_from_filename(filename):
    base_filename = pathlib.Path(filename).name
    author_number, gender, age, industry, star_sign, _ = base_filename.split(".")
    author_number = int(author_number)
    age = int(age)
    return age, author_number, gender, industry, star_sign
  def create_from_attributes(author_number, gender, age, industry, star_sign, post):
    p = Post()
    p.author_number = author_number
    p.gender = gender
    p.age = age
    p.industry = industry
    p.star_sign = star_sign
    #p.date = date
    p.post = post
    return p

y = Post.load_from_file("/content/blogs/801916.female.23.Advertising.Taurus.xml")
d = y[0].to_dict()
print(d)

for filename in get_all_xml_files_in_folder(blogs_ds)[:10]:
  print(filename)

filename_id_pattern = re.compile(r"(\\d{3,})\\..*\\..*\\..*\\..*\\.xml"),

def load_dataset_from_raw(blogs_ds, ids=None):
  all_posts = []
  for filename in get_all_xml_files_in_folder(blogs_ds):
    if ids is None or get_filename_id(filename) in ids:
      current_posts = Post.load_from_file(filename)
      all_posts.extend(current_posts)
  return all_posts

def get_filename_id(filename):
  match = filename_id_pattern.search(filename)
  if match:
    return match.group(1)
  else:
    raise ValueError("Could not find an ID in filename", {filename})

def save_dataset(all_posts, output_file):
  dataset = pd.DataFrame([post.to_dict() for post in all_posts])
  dataset.to_parquet(output_file, compression='gzip')
  return dataset
  
def load_dataset(input_file):
  return pd.read_parquet(input_file)

"""dataset_filename = "blogs_processed.parquet"
all_posts_raw = load_dataset_from_raw(dataset_folder)
print(len(all_posts_raw))
save_dataset(all_posts_raw, dataset_filename)
all_posts = load_dataset(dataset_filename)"""

dataset_filename = "/content/drive/MyDrive/Authorship_Identification/blogs_processed.parquet"
all_posts = load_dataset(dataset_filename)

all_posts

def get_sampled_authors(dataset, sample_authors):
  id_no = dataset['author_number'].isin(sample_authors)
  return dataset[id_no]

sample = get_sampled_authors(all_posts, [3574878, 2845196, 3444474, 3445677, 828046,4284264, 3498812, 4137740, 3662461, 3363271])

documents = sample['post'].values
authors = sample['author_number'].values
documents_train, documents_test, authors_train, authors_test = train_test_split(documents, authors)
from sklearn.feature_extraction.text import TfidfVectorizer
preprocessor = TfidfVectorizer(analyzer='char', ngram_range=(2,3))
X_train = preprocessor.fit_transform(documents_train)
X_test = preprocessor.transform(documents_test)

from sklearn.linear_model import SGDClassifier
model = SGDClassifier()
model.fit(X_train, authors_train)
authors_predicted = model.predict(X_test)
print(classification_report(authors_test, authors_predicted))

