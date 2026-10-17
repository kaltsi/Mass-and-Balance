#!/usr/bin/perl
#
# Bootstrap version of tools/specs_to_json.py.
#
# python3 is not available in this environment, so this perl script produces
# exactly the same JSON (same key names, same ordering, same 2-space indent)
# as the Python converter. Once Python is available, run:
#
#     python3 tools/specs_to_json.py specs/
#
# Usage: specs_to_json.pl aircraft.specs [output_dir]
#        specs_to_json.pl specs/ [output_dir]

use strict;
use warnings;
use utf8;
use File::Basename qw(basename);
use JSON::PP ();   # only for the true/false boolean values

my @LP_TYPES = qw(N R I F C);
my @SAVEABLE = qw(I F C);
my %LIST_KEYS  = map { $_ => 1 } qw(MOMENT_ARMS TOF_MASS_LIMITS LND_MASS_LIMITS);
my %INT_KEYS   = map { $_ => 1 } qw(MOM_DRAW_MAX MASS_DRAW_MAX TRANSLATE_X);
my %FLOAT_KEYS = map { $_ => 1 } qw(LITRE2KILO LND_LIMIT_X1 LND_LIMIT_X2);

sub tonum {
    my $s = shift;
    my $v = 0 + $s;
    return int($v) if $v == int($v);
    return $v;
}

sub parse_load_point {
    my $value = shift;
    my @p = split ' ', $value;
    die "bad load point: $value\n" if @p < 8;

    my $lp = $p[0];
    my $type = substr($lp, 3, 1);
    die "unknown load point type: $lp\n" unless grep { $_ eq $type } @LP_TYPES;

    my $name = substr($lp, 5);

    return {
        LP         => $lp,
        NAME       => $name,
        TYPE       => $type,
        EN         => ($p[1] =~ s/^"|//r) =~ s/"$//r =~ s/#/ /gr,
        FI         => ($p[2] =~ s/^"|//r) =~ s/"$//r =~ s/#/ /gr,
        UNIT       => ($p[3] =~ s/^"|//r) =~ s/"$//r,
        DEFAULT    => tonum($p[4]),
        MIN        => tonum($p[5]),
        MAX        => tonum($p[6]),
        MOMENT_ARM => tonum($p[7]),
        STEP       => @p > 8 ? tonum($p[8]) : undef,
        SAVEABLE   => (grep { $_ eq $type } @SAVEABLE) ? JSON::PP::true : JSON::PP::false,
    };
}

sub parse_specs {
    my $path = shift;
    my (%data, @lps);

    open my $fh, '<:encoding(UTF-8)', $path or die "open $path: $!";
    while (my $line = <$fh>) {
        $line =~ s/^\s+|\s+$//g;
        next if $line eq '' or $line =~ /^#/;
        die "bad line in $path: $line\n" unless $line =~ /=/;

        my ($key, $value) = split '=', $line, 2;
        $value =~ s/^\s+|\s+$//g;

        if ($key eq 'LOAD_POINT') {
            push @lps, parse_load_point($value);
        } elsif ($LIST_KEYS{$key}) {
            $value =~ s/[\[\]]//g;
            $data{$key} = [ map { tonum($_) } split ',', $value ];
        } elsif ($INT_KEYS{$key}) {
            $data{$key} = int(0 + $value);
        } elsif ($FLOAT_KEYS{$key}) {
            $data{$key} = 0 + $value;
        } else {
            $value =~ s/^"|//; $value =~ s/"$//;
            $data{$key} = $value;
        }
    }
    close $fh;

    $data{LOAD_POINTS} = \@lps;
    return \%data;
}

# Python-style JSON writer (2-space indent, sorted keys, no ASCII escaping)
sub encode {
    my ($v, $indent) = @_;
    $indent //= 0;
    my $pad = '  ' x $indent;
    my $pad2 = '  ' x ($indent + 1);

    if (ref $v eq 'HASH') {
        my @keys = sort keys %$v;
        my @out;
        for my $k (@keys) {
            push @out, $pad2 . '"' . $k . '": ' . encode($v->{$k}, $indent + 1);
        }
        return "{\n" . join(",\n", @out) . "\n" . $pad . "}";
    }
    if (ref $v eq 'ARRAY') {
        my @out = map { $pad2 . encode($_, $indent + 1) } @$v;
        return "[\n" . join(",\n", @out) . "\n" . $pad . "]";
    }
    return 'null' unless defined $v;
    return ($$v ? 'true' : 'false') if ref $v eq 'JSON::PP::Boolean';
    return $v if $v =~ /^-?\d+(?:\.\d+)?$/;   # number
    my $s = $v;
    $s =~ s/\\/\\\\/g; $s =~ s/"/\\"/g;
    return '"' . $s . '"';
}

sub convert {
    my ($path, $out_dir) = @_;
    my $base = basename($path);
    my ($name) = $base =~ /^(.*)\./;
    my $data = parse_specs($path);

    my $out = $out_dir ? "$out_dir/$name.json" : "$name.json";
    if ($out_dir) {
        mkdir $out_dir unless -d $out_dir;
    }

    open my $fh, '>:encoding(UTF-8)', $out or die "open $out: $!";
    print $fh encode($data) . "\n";
    close $fh;
    print $out, "\n";
}

my ($target, $out_dir) = @ARGV;
die "Usage: $0 aircraft.specs [output_dir]\n" unless $target;
$target =~ s{/+$}{};
$out_dir =~ s{/+$}{} if $out_dir;

if (-d $target) {
    for my $f (sort grep { /\.specs$/ } glob("$target/*.specs")) {
        convert($f, $out_dir || $target);
    }
} else {
    convert($target, $out_dir);
}
