#!/usr/bin/env perl
use strict;
use warnings;

my @headers = qw(
    id latency ue_id ran_ue_id
    PdcpSduVolumeDL PdcpSduVolumeUL
    RlcSduDelayDl UEThpDl UEThpUl
    PrbTotDl PrbTotUl
);

print join(",", @headers), "\n";

my @entries;
my %current_entry;
my $current_id;
my $current_latency;

while (<>) {
    chomp;

    if (/^\s*(\d+)\s+KPM ind_msg latency\s*=\s*(\d+)/) {
        for my $entry (@entries) {
            print_entry($entry, \@headers) if is_complete($entry, \@headers);
        }
        @entries = ();
        $current_id = $1;
        $current_latency = $2;
        %current_entry = ();
    }
    elsif (/amf_ue_ngap_id\s*=\s*(\d+)/) {
        $current_entry{ue_id} = $1;
        $current_entry{id} = $current_id;
        $current_entry{latency} = $current_latency;
    }
    elsif (/ran_ue_id\s*=\s*(\d+)/) {
        $current_entry{ran_ue_id} = $1;
    }
    elsif (/PdcpSduVolumeDL\s*=\s*(\d+)/) {
        $current_entry{PdcpSduVolumeDL} = $1;
    }
    elsif (/PdcpSduVolumeUL\s*=\s*(\d+)/) {
        $current_entry{PdcpSduVolumeUL} = $1;
    }
    elsif (/RlcSduDelayDl\s*=\s*([\d.]+)/) {
        $current_entry{RlcSduDelayDl} = $1;
    }
    elsif (/UEThpDl\s*=\s*([\d.]+)/) {
        $current_entry{UEThpDl} = $1;
    }
    elsif (/UEThpUl\s*=\s*([\d.]+)/) {
        $current_entry{UEThpUl} = $1;
    }
    elsif (/PrbTotDl\s*=\s*(\d+)/) {
        $current_entry{PrbTotDl} = $1;
    }
    elsif (/PrbTotUl\s*=\s*(\d+)/) {
        $current_entry{PrbTotUl} = $1;
        push @entries, { %current_entry };
        %current_entry = ();
    }
}

for my $entry (@entries) {
    print_entry($entry, \@headers) if is_complete($entry, \@headers);
}

sub is_complete {
    my ($entry, $headers) = @_;
    for my $key (@$headers) {
        return 0 unless exists $entry->{$key};
    }
    return 1;
}

sub print_entry {
    my ($entry, $headers) = @_;
    print join(",", map { $entry->{$_} } @$headers), "\n";
}
