# EXFOR Entry's DOI Information

This repository contains a script and output files (Pickle or JSON) for obtaining DOIs (Digital Object Identifiers) for EXFOR entries that lack DOI information in the original EXFOR format.

## General Information

The script `parse_crossref.py` retrieves DOIs using the title (`TITLE`) and the first author's name (`AUTHOR`) for each EXFOR entry. It follows these steps:

1. The [EXFOR parser](https://github.com/IAEA-NDS/exforparser) converts EXFOR entries from the [EXFOR Master](https://github.com/IAEA-NDS/exfor_master) repository into an SQL database (SQLite file).
2. The script loads bibliographic information of EXFOR entries that lack DOI information from the database.
3. It then queries the Crossref API to find the corresponding DOI.
4. The returned bibliographic data from the Crossref API is analyzed by checking the similarity of the article title and the family name of the first author using `SequenceMatcher` from `difflib`.
5. If the similarities of both the article title and family name exceed 0.8 (80%), the DOI is assigned to the entry’s bibliographic data.
6. Results are stored into [`data/doi.json`](data/doi.json) and `data/doi.pickle`.

### Example Crossref API Query

The script constructs queries like the following to search for DOI information:

```
https://api.crossref.org/works?query.title=18O+48Ti%20elastic%20and%20inelastic%20scattering%20at%20275%20MeV&query.bibliographic=2024,Brischetto.&select=title,author,DOI&rows=20
```

**Note:** Crossref API usage does not have limitations, but requests must include a `mailto` contact in the request header.

### References & Documentation of Crossref
- [Crossref API Documentation](https://api.crossref.org/swagger-ui/index.html)
- [Crossref REST API Guide](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
- [Crossref Guest Query](https://www.crossref.org/guestquery/)

### Requirements

To run the script, ensure you have the following dependencies installed:

```sh
pip install -r requirements.txt
```

### Usage

The retrieved DOIs are stored in either:
- **Pickle (`.pickle`) format**: Serialized Python objects.
- **JSON (`.json`) format**: Human-readable structured data.

Load the pickle file into a Pandas DataFrame using:

```python
import pandas as pd
df = pd.read_pickle("data/doi.pickle")
print(df)
```

Run the script using:

```sh
python -m parse_crossref
```


## License

This repository is licensed under the MIT License. See [LICENSE](LICENSE) for details.

