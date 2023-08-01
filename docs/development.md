# Development

Contributions are welcome and appreciated!

We are glad you are here and appreciate your contribution. Please keep in mind
our
[community participation guidelines](https://github.com/InsightSoftwareConsortium/ITK/blob/master/CODE_OF_CONDUCT.md).

To run the unit tests:

```sh
pip install -e ".[test,dask-image,itk,cli]"
pre-commit install
pytest
```

### Updating test data

1. Generate new test data tarball

```
cd test/data
tar cvf ../data.tar baseline input
gzip -9 ../data.tar
```

2. Upload the data to [web3.storage](https://web3.storage)

3. Upload the `test_data_ipfs_cid` (from web3.storage web UI) and
   `test_data_sha256` (`sh256sum ../data.tar.gz`) variables in _test/\_data.py_.
