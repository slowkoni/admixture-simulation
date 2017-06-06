# Admixture simulation tool

Simulates admixed individuals from input individuals of presumed or known single-population origin using Wright-Fisher forward simulation for a small number of generations. This tool is intended to aid development and testing of tools which analyze the genomes of admixed individuals, such as local ancestry inference.

### To build the docker image

Change to the directory containing the github repo.

```
docker build --build-arg UID=$UID -t admixture-simulation admixture-simulation
```

This will build the image tagged with the name "admixture-simulation" and add it to your collection of images.

### To execute an admixture simulation

First, you need an input VCF (or BCF) file and a sample map file. You can use real data, though you need to be certain that samples are from a single ancestry. Any sample in the input VCF which is not mentioned in the sample map file is not included in the simulation, so an easy way to exclude any samples you are uncertain about is to simply exclude the sample id from the sample map file, or comment it out with a leading #. To generate data _de novo_, see [out-of-africa](https://github.com/slowkoni/out-of-africa) _de novo_ simulation tool.

The sample map file is a two column tab delimited text file giving VCF sample ids (those that appear on the #CHROM header line) in the first column and the label/name of the corresponding subpopulation in the second column. Any following columns are ignored. Suppose your VCF and sample map file are named my-input.vcf.gz and my-input.map, and located at the absolute path directory /path/to/input/files/ on the docker host.

```
docker run -t -i -v /path/to/input/files:/home/admixture-simulation/shared admixture-simulation --input-vcf shared/my-input.vcf.gz --sample-map shared/my-input.map --output-basename test-admix --chromosome 20 --n-generations 8 --n-output 100
```

If the input data is simulated and only contains one chromosome, make sure you select the right chromosome with the --chromosome option. Otherwise, for whole genome VCF inputs, this container only simulates one chromosome, so you must select which one with the --chromosome option. This option defaults to chromosome 20. To see all available command options, use ```docker run -t -i admixture-simulation -h```

### Output

Several files will be created in the same directory as the input VCF data (or whatever was mapped to /home/admixture/shared inside the container), with the leading prefix ```test-admix``` (in example command above) or whatever is specified by the required --output-basename option. 

File                           | Purpose
------------------------------ | -------
test-admix.founders.bcf.gz     | BCF file containing input VCF samples selected as founders for admixed population
test-admix.founders.bcf.gz.csi | corresponding index for above
test-admix.ref.bcf.gz          | BCF file containing input VCF samples _not_ selected as founders
test-admix.ref.bcf.gz.csi      | corresponding index for above
test-admix.query.vcf           | VCF file containing simulated admixed samples
test-admix.result              | Tab delimited matrix indicating population of origin for each admixed _haplotype_

The .ref.bcf.gz file is suitable for use as reference haplotypes in testing local ancestry analysis tools because the haplotypes which generated the testing data (test-admix.query.vcf) are not present. Half of the convenience of this tool is it seperates the founders from what you will retain as reference data for you and saves you the trouble of performing this chore. You simply provide what you might otherwise provide directly as reference data to the local ancestry tool, and this tool will create a new reference dataset for you with the data used for generating simulated test cases removed. You will probably not need the founders files but they are created anyway. Any sample not listed in the sample map file is not included in either the founders or the ref output files. In the case of RFMIX, the sample input sample map may be used with the new reference file created here, as samples defined in the sample map which do not appear in the reference VCF input are simply ignored.

The .result file has one line for each variant in the input VCF, and all output VCF/BCF files contain a line for each input VCF variant, regardless of whether or not the variant is segregating among the samples in the file. The .result file will have two consecutive columns for every corresponding sample column in .query.vcf, one for each haplotype. The entries of the tab delimited matrix are integer codes starting from 1 and correspond to the population labels in the input sample map file in the order they first appear.
