``pygpw`` is a python module that uses a trigraph probability matrix (extracted from an english dictionary) to pseudo-randomly generate pronouncable words. This can be used for creating new non-dictionary passwords that are easy to remember, and it can also be fantastic for helping come up with creative names.

``pygpw`` is released under the zlib license. Note that this ``pygpw`` is not the same as the "pygpw" on google code *(which was created and published after this project, and also has less features)*.

Inspired by `existing C++ and Java implementations <http://www.multicians.org/thvv/gpw.html>`_ and [1]_, pygpw offers added functionality, such as multiple pronouncability methods and leetification , as well as a flexible command line interface. 

------------------

Here is some sample usage::

    $ pygpw 6

    ariblene
    instormi
    expassac
    andishia
    tumircop
    zonester

The above set of 6 words were generated using the trigraph method (default). Compare this with purely random words::
	
    $ pygpw 3 --method=random

    lrdcpvku
    yzbwscvk
    obnfwsoa

A slightly faster naive method is provided which simply ensures two consonants are never together::
	
    $ pygpw 4 --method=naive --length=10

    meholeweot
    ejiroeouvu
    taruituquo
    bayuwifale

Here is an example of leetification::
	
    $ pygpw 3 --1337

    h|@|oCH3
    !Ch0b@R2
    !NeS5!b3

How did that happen? How am I meant to remember that password? Let's use the explain flag::
	
    $ pygpw 3 --1337 --explain

    h|@|oCH3 (hialoche)
    !Ch0b@R2 (ichobarr)
    !NeS5!b3 (inessibe)

Leetification is done through capitalisation flipping and random subsitution (via lookup tables). There are two levels of substitution: single character (default) or multicharacter substitutions. Following is an example of multicharacter substitution; note that in this case, the --length restriction applies to the final word length, not the source word length::
	
    $ pygpw 3 -L12 --leetify --multichar --explain

    r&P/-\T!/|\5 (repatims)
    t4|e|2PoR$EL (talerporsel)
    |2OMBAPi<@|~ (rombapicar)

The frequency of captilisation flipping and substitution can also be controlled::
	
    # flip all to capitals, do zero substitutions
    $ pygpw 3 --1337 -s0 -c1

    TONFIERT
    WHOLYSTA
    BLETTICA
     
    # never flip capitals, always try to substitute
    $ pygpw 3 --1337 -s 1 -c 0

    ||m0z|m8
    ~{&21f+&
    371{0^dd
     
    # 30% chance to flip capitals, 20% chance to substitute
    $ pygpw 3 --1337 -s0.2 -c0.3

    fie2g3A~
    OleCtorp
    OlygoNt&

And finally, if you are trying to generate more secure passwords, you may want to use an expanded character set (+alphanumeric, +symbols)::
	
    $ pygpw 3 -qxl32

    [Y-:s=Kl(ZXZ$AgM+"m@8e0"Uy<OfrBt
    vS0<code>gR+u#1j#U\8)>v:Bl=(CjBr}K{;2
    P$$F65</code>uw@_pJ=]>&=o=N!rPE'A4P:b2

-----------------

Full pygpw usage::
	
    Usage: pygpw [options] <numpasswords>
     
    Options:
      -h, --help            show this help message and exit
      -l PWDLEN, -L PWDLEN, --length=PWDLEN
                            The length of each password (default 8)
      -q, --quiet           Supress printing of errors and warnings
      --version             Show version number
     
      Pronouncability Options:
        For choosing the pronouncability algorithm used
     
        -m METHOD, --method=METHOD
                            Where METHOD is the level of pronouncability:
                            ['trigraph', 'naive', 'random']
        -x, --expanded      Use an expanded random character set
                            (produces unpronouncable words, forces METHOD to
                            'random')
     
      Leetification Options:
        For choosing leetify level
     
        --1337, --leetify   Performs a 'leet' -> '1337' style substitution.
                            (ignored if METHOD is 'random', all leetification
                            options only apply when this flag is set)
        -e, --explain       Explain the leetification by showing source
        --multichar         include multi-character leetification ('m' -> '/V\')
        -c CAP_FREQ, --capitalize-freq=CAP_FREQ
                            Possibility of captilization flipping of a character
                            (default=0.5)
        -s SUBST_FREQ, --substitution-freq=SUBST_FREQ
                            Possibility of leetification of a character
                            (default=0.5)

If you haven't already, grab ``pygpw`` and give it a try!

.. [1] Gasser, M., A Random Word Generator for Pronouncable Passwords, MTR-3006, The MITRE Corporation, Bedford, MA 01730, ESD-TR-75-97, HQ Electronic Systems Division, Hanscom AFB, MA 01731. NTIS AD A 017676.

