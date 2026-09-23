JOYPOP Local V5.22 patch
- Added HAR card data for goods_id: 10,12,14,15,16,19,20,21
- Added card albums/pools/rates captured from joypop3.gg HAR
- Added mirrored image assets available in the HAR
- Keeps V5.21 order_interval_num pack grouping fix

Install: copy everything in this patch over ~/joypop-local/ and allow overwrite.
Then restart: pkill -f server_v5_13.py ; python3 -u server_v5_13.py
