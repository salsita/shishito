# Shishito documentation

## Requirements

Documentation uses Sphinx (for doc see http://sphinx-doc.org). You can install sphinx using pip:

``` pip install -U Sphinx ```

## Generete doc from code comments

If you want to generate documentation from shishito source codes, you have to run following command (from doc directory):

``` sphinx-apidoc -M -f -o source ../shishito  ```

or run generate_doc.sh in doc folder.

## Build doc

To build documentations (create html pages) run make in doc folder:

``` make html ```

Generated files will be created in build folder. Entry point for documentation is index.html.
