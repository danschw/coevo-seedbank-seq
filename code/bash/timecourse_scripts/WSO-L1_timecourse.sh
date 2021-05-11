#!/bin/bash
#SBATCH --mail-user=danschw@iu.edu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --time=9:59:00
#SBATCH --mem=50gb
#SBATCH --mail-type=FAIL,BEGIN,END
#SBATCH --job-name=WSO-L1

##### load dependencies #####
module load samtools
module unload python
module load python/2.7.16

samtools mpileup -q10 -f /N/slate/danschw/coevo-seedbank-seq/data/map-EVOL/phage/breseq2/WSO-L1-T1/data/reference.fasta /N/slate/danschw/coevo-seedbank-seq/data/map-EVOL/phage/breseq2/WSO-L1-T10/data/reference.bam /N/slate/danschw/coevo-seedbank-seq/data/map-EVOL/phage/breseq2/WSO-L1-T14/data/reference.bam /N/slate/danschw/coevo-seedbank-seq/data/map-EVOL/phage/breseq2/WSO-L1-T1/data/reference.bam /N/slate/danschw/coevo-seedbank-seq/data/map-EVOL/phage/breseq2/WSO-L1-T4/data/reference.bam /N/slate/danschw/coevo-seedbank-seq/data/map-EVOL/phage/breseq2/WSO-L1-T7/data/reference.bam > /N/slate/danschw/coevo-seedbank-seq/data/timecourses/phage/timecourse_merged/WSO-L1.pileup

cat /N/slate/danschw/coevo-seedbank-seq/data/timecourses/phage/timecourse_merged/WSO-L1.pileup | python /N/slate/danschw/coevo-seedbank-seq/code/python/create_timecourse.py WSO-L1 10 14 1 4 7 > /N/slate/danschw/coevo-seedbank-seq/data/timecourses/phage/timecourse_merged/WSO-L1_timecourse.txt