#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import argparse
import random
import re

# wrapper to stop this script from trying to progress if any of the many
# shell commands it executes fails or the user interrupts with ctrl-c
# as the latter stops the shell command but not this script
def run_shell_cmd(cmd):
    rval = os.system(cmd)
    if rval != 0:
        signal = rval & 0xFF
        exit_code = rval >> 8
        if signal != 0:
            sys.stderr.write("\nCommand %s exits with signal %d\n\n" % (cmd, signal))
            sys.exit(signal)
        sys.stderr.write("\nCommand %s failed with return code %d\n\n" % (cmd, exit_code))
        sys.exit(exit_code)

# extracts specified samples from a vcf/bcf file and outputs a new indexed
# BCF file. Since bcftools does not like 2nd or following columns, we cut
# off the first column with the sample ids. The second will typically
# have the subpopulation label in this context
def subsample_vcf_samples(output_fname, input_fname, samples_fname):
    run_shell_cmd("cat %s | cut -f 1 | bcftools view --output-type b --output-file %s --samples-file - --threads 12 %s" % (samples_fname, output_fname, input_fname))
    run_shell_cmd("bcftools index -f %s" % (output_fname))

# For debugging mainly, when I want to see the command that is actually
# built by a string formatting and is attempting to execute
def print_and_run(cmd):
    print(cmd)
    run_shell_cmd(cmd)


cmdline = argparse.ArgumentParser(description="Use a phased reference panel to generate simulated admixed samples using Wright-Fisher random mating forward simulation. A percentage of samples are selected at random as founders for the admixed samples and a new reference panel excluding these founders is output. Local ancestry analysis on the simulated admixed samples should not use the original input reference panel as this contains samples with the exact founding haplotypes.")
cmdline.add_argument("--input-vcf",help="Input VCF/BCF file",type=str, required=True)
cmdline.add_argument("--sample-map",help="Map file mapping VCF sample ids to populations for input VCF",type=str,required=True)

cmdline.add_argument("--parent-percent",help="Select specified percentage of samples (at random) as parents for breeding the admixed population", type=float, default=10)
cmdline.add_argument("--n-output",help="Maximum number of diploid individuals to output", type=int, default=-1, required=False)
cmdline.add_argument("--chromosome",help="Chromosome to select for simulation (only one chromosome is used)",type=int,default=20)
cmdline.add_argument("--genetic-map",help="Genetic map file for corresponding chromosome",type=str,default="hapmap-phase2-genetic-map.tsv.gz")
cmdline.add_argument("--n-generations",help="Number of generations of random-mating admixture to simulate. Must be two or larger.",type=int,default=8)
cmdline.add_argument("--dephase",help="Output unphased data for admixed samples",action="store_true",default=False)
cmdline.add_argument("--phase-switch",help="Introduce phase switches at specified rate (verification data is not switched)",type=float,default=0.0)

cmdline.add_argument("--output-basename",help="Output prefix/basename for simulated samples and reference panel with parents removed",type=str,default="",required=True)
cmdline.add_argument("--random-seed",help="Set random seed for simulaton. Default is fixed value",type=int,default=0xDEADBEEF,required=False)

args = cmdline.parse_args()
p = args.parent_percent / 100.

# If we have VCF input, convert it to compressed BCF so we can index it
if args.input_vcf.endswith(('.vcf','.vcf.gz','.vcf.bgz')):
    tmp = re.sub('.vcf(|.gz|.bgz)$','.bcf.gz',args.input_vcf)
    run_shell_cmd("bcftools view --output-type b --output-file %s --threads 12 %s" % (tmp,args.input_vcf))
    args.input_vcf = tmp

run_shell_cmd("bcftools index -f %s" % (args.input_vcf))


# Randomly select the founders. Note that we are not attempting to ensure
# that each population is equally represented. In expectation, each
# population will be represented in the same proportion it occurs in the
# input VCF file
founder_map = {}
reference_map = {}

f = open(args.sample_map, 'r')
founder_map = open("%s.founders.map" % args.output_basename, "w")
reference_map = open("%s.ref.map" % args.output_basename, "w")

random.seed(args.random_seed)
for line in f:
    [id, subpop] = line.strip().split('\t')
    if random.random() < p:
#        founder_map[id] = subpop
        founder_map.write("%s\t%s\n" % (id, subpop))
    else:
        reference_map.write("%s\t%s\n" % (id, subpop))
#        reference_map[id] = subpop
        
        
f.close()
founder_map.close()
reference_map.close()

# Split off the founders and create a new reference BCF file that excludes
# them, so the "testing data" is not included with the "training data"
subsample_vcf_samples("%s.founders.bcf.gz" % args.output_basename, args.input_vcf, "%s.founders.map" % args.output_basename)
subsample_vcf_samples("%s.ref.bcf.gz" % args.output_basename, args.input_vcf, "%s.ref.map" % args.output_basename)

# Right now the simulate command doesn't recognize or internally decompress
# a compressed genetic map. The hapmap phase2 and probably most other
# human genetic maps out there are large and may be compressed. The one
# we are going to include internally here is larger than the github
# recommended max file size, so we are going to store it compressed
remove_map = False
if args.genetic_map.endswith(('.gz','.bgz')):
    tmp = re.sub('\.(bgz|gz)$','',args.genetic_map);
    run_shell_cmd("gzip -dc %s > %s" % (args.genetic_map, tmp))
    args.genetic_map = tmp
    remove_map = True

# Do the actual forward random-mating simulation using RFMIX's tool
# that was built for this purpose, but assumes the entire input VCF/BCF
# is founders of the admixing population, thus we need all the above to
# get here
print_and_run("rfmix/simulate -f %s.founders.bcf.gz -m %s.founders.map -g %s -o %s --growth-rate=1.5 --maximum-size=2000 --n-output=%d -c %d -G %d -p %f --random-seed=%d %s" % (args.output_basename, args.output_basename, args.genetic_map, args.output_basename, args.n_output, args.chromosome, args.n_generations, args.phase_switch, args.random_seed, "--dephase" if args.dephase else ""))

# If we decompressed the map, get rid of the decompressed file to keep
# shit clean
if remove_map:
    run_shell_cmd("rm -f %s" % args.genetic_map)

