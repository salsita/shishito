Utilities
====================================================

Various tools and utilities used during testing

## HTML report generation

Test results HTML report generated from provided XSL template.

### Example use (with Continuous Integration)

Bellow, you can find example bash script that executes tests, generates HTML report and exits with appropriate exit code (based on the test results).

```
#!/bin/bash
######################
# VARIABLES          #
######################

root_folder=src/integration_tests
xlst_name=xunit_to_html.xslt
search_string=failure
search_extensions=*.xml

######################
# SCRIPT             #
######################

# Run tests
python ${root_folder}/pytest_runner.py

# Create HTML reports
find ${root_folder}/results/ -type f -name "${search_extensions}" | while read file; do xsltproc ${root_folder}/utils/${xlst_name} ${file} > ${file:0:-4}.html; done

# Search reports for failures and return appropriate exit code
result=$(grep ${search_string} $(find ${root_folder}/results/ -type f -name "${search_extensions}"))
if [ "$result" == "" ]; then
    echo "No failures found."
    exit 0
else
    echo "failures found!" ${result}
    exit 1
fi
```