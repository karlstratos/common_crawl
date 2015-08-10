Code for extracting text from Common Crawl
==========================================
Download the file listing URLs to WET files and correct it:

`sed -i 's/common/https\:\/\/aws\-publicdatasets\.s3\.amazonaws\.com\/common/g' wet.paths`

Give the URLs to a python script to download extracted, cleaned text files:

`python3 download_clean.py wet.paths downloaded`

To remove files that are essentially empty, use:

`ls -l downloaded/ | awk '{if(NF > 2 && $5+0 < 100) printf("downloaded/%s\n",$9);}' | xargs rm`

To randomly sample 100 files, use:

`cp $(ls -l downloaded | tail -8581 | shuf | head -100 | awk '{printf("downloaded/%s\n",$9);}') downloaded_rand100`
