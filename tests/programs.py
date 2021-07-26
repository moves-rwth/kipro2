brp = """ # The number of total packages to send
nat toSend;

# Number of packages sent
nat sent;

# The maximal number of retransmission tries
nat maxFailed;

# The number of failed retransmission tries
nat failed;

nat totalFailed;

while(failed < maxFailed & sent < toSend){
    {
        # Transmission of current packages successful
        failed := 0;
        sent := sent + 1;
    }
    [0.9]
    {
        # Transmission not successful
        failed := failed +1;
        totalFailed := totalFailed + 1;
    }
}
"""


geo = """nat c;
nat f;

while(f=1){
   {f := 0}[0.5]{c := c+1}
}"""


rabin = """nat i;
nat n; # Does not need to be initialized
nat d;

nat phase; # Initially 0
while(1<i || phase=1){
    if(phase=0){
      n:=i;
      phase:=1;
    }{
        if(0<n){
            {d:=0}[0.5]{d:=1};
            i:=i-d;
            n:=n-1;
        }{ #leave inner loop
            phase:=0;
        }
     }
}"""


unif_gen = """# Adapted form http://www-i2.informatik.rwth-aachen.de/pub/index.php?type=download&pub_id=1233, which in turn adapted from
# Jérémie Lumbroso. Optimal Discrete Uniform Generation from Coin Flips, and Applications.
# In: CoRR abs/1304.1916 (2013).

# We want to model uniform(elow,...,ehigh)
nat elow;
nat ehigh; # Initially elow <= ehigh
nat n; # Initially ehigh-elow + 1
nat v; # Initially 1
nat c; # Initially 0; the result
nat running; # Initially 0

nat i; # auxiliary variable for array positions in specifications

while(running = 0){

    v := 2*v;
    {c := 2*c+1}[0.5]{c := 2*c};
    if((not (v<n))){
        if((not (n=c)) & (not (n<c))){ # terminate
            running := 1
        }{
            v := v-n;
            c := c-n;
        }
    }{
        skip
    }

    # On termination, determine correct index
    if((not (running = 0))){
        c := elow + c;
    }{
        skip
    }
}"""