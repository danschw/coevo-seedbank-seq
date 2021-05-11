#!/bin/bash
#SBATCH --mail-user=danschw@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --time=9:59:00
#SBATCH --mem=50gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=WSO-L3-T14-rS

##### load dependencies #####
module load r
module load bowtie2

##### run breseq from local instance #####
/N/u/danschw/Carbonate/my_tools/breseq-0.35.5-Linux-x86_64/bin/breseq -j 8 -p --brief-html-output --polymorphism-reject-indel-homopolymer-length 0 --polymorphism-reject-surrounding-homopolymer-length 0 --polymorphism-score-cutoff 2 -o /N/slate/danschw/coevo-seedbank-seq/data/map-EVOL/host/breseq1/WSO-L3-T14-rS -r /N/slate/danschw/coevo-seedbank-seq/data/delta6-ANC2.gff3 /N/slate/danschw/coevo-seedbank-seq/data/ddup-fastq/host/ddup-GSF2865-WSO-L3-T14-rS_S43_R1_001.fastq.gz /N/slate/danschw/coevo-seedbank-seq/data/ddup-fastq/host/ddup-GSF2865-WSO-L3-T14-rS_S43_R2_001.fastq.gz > /N/slate/danschw/coevo-seedbank-seq/data/map-EVOL/host/breseq1_err/WSO-L3-T14-rS.err 2> /N/slate/danschw/coevo-seedbank-seq/data/map-EVOL/host/breseq1_log/WSO-L3-T14-rS.log