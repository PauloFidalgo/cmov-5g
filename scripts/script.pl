
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

my %entry;
while (<>) {
    chomp;

    if (/^\s*(\d+)\s+KPM ind_msg latency\s*=\s*(\d+)/) {
        # Print previous entry if exists
        print join(",", map { $entry{$_} // "" } @headers), "\n" if %entry;
        %entry = ();  # Reset
        $entry{id} = $1;
        $entry{latency} = $2;
    }
    elsif (/amf_ue_ngap_id\s*=\s*(\d+)/) {
        $entry{ue_id} = $1;
    }
    elsif (/ran_ue_id\s*=\s*(\d+)/) {
        $entry{ran_ue_id} = $1;
    }
    elsif (/PdcpSduVolumeDL\s*=\s*(\d+)/) {
        $entry{PdcpSduVolumeDL} = $1;
    }
    elsif (/PdcpSduVolumeUL\s*=\s*(\d+)/) {
        $entry{PdcpSduVolumeUL} = $1;
    }
    elsif (/RlcSduDelayDl\s*=\s*([\d.]+)/) {
        $entry{RlcSduDelayDl} = $1;
    }
    elsif (/UEThpDl\s*=\s*([\d.]+)/) {
        $entry{UEThpDl} = $1;
    }
    elsif (/UEThpUl\s*=\s*([\d.]+)/) {
        $entry{UEThpUl} = $1;
    }
    elsif (/PrbTotDl\s*=\s*(\d+)/) {
        $entry{PrbTotDl} = $1;
    }
    elsif (/PrbTotUl\s*=\s*(\d+)/) {
        $entry{PrbTotUl} = $1;
    }
}

# Print last entry
print join(",", map { $entry{$_} // "" } @headers), "\n" if %entry;