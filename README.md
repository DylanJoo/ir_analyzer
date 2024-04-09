```
mkdir -p documents/
for file in raw_data/*/10-K/*jsonl;do
    python3 preprocess/split_corpus.py \
        --input_jsonl $file \   # the jsonl with entire document.
        --output_dir documents/ # all documents would output here.
done
```
