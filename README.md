0. Empty and renew the database
```
rm db/relevation.db
python manage.py migrate --run-syncdb
```

1. Download corpus
Here we use TREC-COVID as an example. 
```
mkdir data
wget https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/trec-covid.zip -P data/
cd data
unzip trec-covid.zip
rm trec-covid.zip
```
For efficiency, we will use one `docid` as one file in the [documents](documents/) directory. This is supposed to run only once. You can use the `split_corpus.py` scripts:
```
mkdir -p documents/
python3 tools/split_corpus.py \
    --input_jsonl <corpus.jsonl>  \   # the jsonl file of entire corpus.
    --output_dir documents/           # save documents  here.
```

2. Acquire/download qrels
```
wget https://github.com/castorini/anserini-tools/raw/6841ccdbe4ca6d39549c794396d365d68d279715/topics-and-qrels/qrels.beir-v1.0.0-trec-covid.test.txt -P data/
```

3. Setup queries, baseline results and compared results
Check the setup section on the navigation bar, and upload the files with formats accordingly.
```
python manage.py runserver
```
