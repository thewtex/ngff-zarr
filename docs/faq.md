# 🤔 Frequently Asked Questions (FAQ)

## Performance and Memory

### Why does `to_multiscales` perform computation immediately with large datasets?

For both small and large datasets, `to_multiscales` returns a simple Python
dataclass composed of basic Python datatypes and lazy dask arrays. The lazy dask
arrays, as with all dask arrays, are a task graph that defines how to generate
those arrays and do not exist in memory. This is the case for both regular sized
datasets and very large datasets.

For very large datasets, though, data conditioning and task graph engineering is
performed during construction to improve performance and avoid running out of
system memory. This preprocessing step ensures that when you eventually compute
the arrays, the operations are optimized and memory-efficient.

If you want to avoid this behavior entirely, you can pass `cache=False` to
`to_multiscales`:

```python
multiscales = to_multiscales(image, cache=False)
```

**Warning:** Disabling caching may cause you to run out of memory when working
with very large datasets!

The lazy evaluation approach allows ngff-zarr to handle extremely large datasets
that wouldn't fit in memory, while still providing optimal performance through
intelligent task graph optimization.
