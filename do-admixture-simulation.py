#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import argparse
import random
import re

def subsample_vcf_samples(output_fname, input_fname, samples_fname):
    os.system("cat %s | cut -f 1 | bcftools view --output-type b --output-file %s --samples-file - --threads 12 %s" % (samples_fname, output_fname, input_fname))
    os.system("bcftools index %s" % (output_fname))

def print_and_run(cmd):
    print(cmd)
    os.system(cmd)


cmdline = argparse.ArgumentParser(description="Use a phased reference panel to generate simulated admixed samples using Wright-Fisher random mating forward simulation. A percentage of samples are selected at random as founders for the admixed samples and a new reference panel excluding these founders is output. Local ancestry analysis on the simulated admixed samples should not use the original input reference panel as this contains samples with the exact founding haplotypes.")
cmdline.add_argument("--input-vcf",help="Input VCF/BCF file",type=str, required=True)
cmdline.add_argument("--sample-map",help="Map file mapping VCF sample ids to populations for input VCF",type=str,required=True)

cmdline.add_argument("--parent-percent",help="Select specified percentage of samples (at random) as parents for breeding the admixed population", type=float, default=10)
cmdline.add_argument("--n-output",help="Maximum number of diploid individuals to output", type=int, default=-1, required=False)
cmdline.add_argument("--chromosome",help="Chromosome to select for simulation (only one chromosome is used)",type=int,default=20)
cmdline.add_argument("--n-generations",help="Number of generations of random-mating admixture to simulate. Must be two or larger.",type=int,default=8)
cmdline.add_argument("--dephase",help="Output unphased data for admixed samples",action="store_true",default=False)
cmdline.add_argument("--phase-switch",help="Introduce phase switches at specified rate (verification data is not switched)",type=float,default=0.0)

cmdline.add_argument("--output-basename",help="Output prefix/basename for simulated samples and reference panel with parents removed",type=str,default="",required=True)
cmdline.add_argument("--random-seed",help="Set random seed for simulaton. Default is fixed value",type=int,default=0xDEADBEEF,required=False)

args = cmdline.parse_args()
p = args.parent_percent / 100.

if args.input_vcf.endswith(('.vcf','.vcf.gz','.vcf.bgz')):
    tmp = re.sub('.vcf(|.gz|.bgz)$','.bcf.gz',args.input_vcf)
    os.system("bcftools view --output-type b --output-file %s --threads 12 %s" % (tmp,args.input_vcf))
    args.input_vcf = tmp

os.system("bcftools index %s" % (args.input_vcf))

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

subsample_vcf_samples("%s.founders.bcf.gz" % args.output_basename, args.input_vcf, "%s.founders.map" % args.output_basename)
subsample_vcf_samples("%s.ref.bcf.gz" % args.output_basename, args.input_vcf, "%s.ref.map" % args.output_basename)

#os.system("cat %s.founders.map | cut -f 1 | bcftools view --output-type b --output-file %s.founders.bcf.gz --samples-file - --threads 12 %s" % (args.output_basename, args.output_basename, args.input_vcf))

#os.system("cat %s.ref.map | cut -f 1 | bcftools view --output-type b --output-file %s.ref.bcf.gz --samples-file - --threads 12 %s" % (args.output_basename, args.output_basename, args.input_vcf))

print_and_run("rfmix/simulate -f %s.founders.bcf.gz -m %s.founders.map -g %s -o %s --growth-rate=1.5 --maximum-size=2000 --n-output=%d -c %d -G %d -p %f --random-seed=0xDEADBEEF" % (args.output_basename, args.output_basename, "hapmap-phase2-genetic-map.tsv", args.output_basename, args.n_output, args.chromosome, args.n_generations, args.phase_switch))

