# 💾 Installation

::::{tab-set}

:::{tab-item} System

```shell
pip install "ngff-zarr[cli]"
```

:::

:::{tab-item} Browser In Pyodide, e.g. the
[Pyodide REPL](https://pyodide.org/en/stable/console.html) or
[JupyterLite](https://jupyterlite.readthedocs.io/en/latest/try/lab),

```python
import micropip
await micropip.install('ngff-zarr')
```

:::

::::

Optional dependencies include:

`cli` : Additional IO libraries for the command line interface (CLI).

`dask-image` : Multiscale generation with `dask-image` methods.

`itk` : Multiscale generation with `itk` methods.
