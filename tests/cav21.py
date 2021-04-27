# Provide 5- as well as 1-inductive invariant
brp = """
   # Adapted from Jip's MA
   # The number of total packages to send
   nat toSend;

   # Number of packages sent
   nat sent;

   # The maximal number of retransmission tries
   nat maxFailed;

   # The number of failed retransmission tries
   nat failed;

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
      }
   }
"""

# BRP + total count? (for a non-1-bounded example) <<<<<<<<<< consider this

# Rabin Mutual exclusion?


# Verify all hoffmann examples?

# Random number ?
random_number_generator = """
# Adapted form http://www-i2.informatik.rwth-aachen.de/pub/index.php?type=download&pub_id=1233, which in turn adapted from
# Jérémie Lumbroso. Optimal Discrete Uniform Generation from Coin Flips, and Applications.
# In: CoRR abs/1304.1916 (2013).

# We want to model uniform(elow,...,ehigh)

nat n; # number of elemtns we want to sample from {0,...,n-1}
nat v; # Initially 1
nat c; # Initially 0; the result 
nat running; # Initially 0

nat i; # auxiliary variable for array positions in specifications

while(running = 0){

    v := 2*v;
    {c := 2*c+1}[0.5]{c := 2*c};
    if(n<=v){
        if(c<n){ # terminate
            running := 1
        }{
            v := v-n;
            c := c-n;
        }
    }{}
}
"""

post = "[c=i]"
pre = "[n=5 & v=1 & c=0 & running=0]*(1/5) + [not (n=5 & v=1 & c=0 & running=0)]*1"

# Rabin


"""

    nat i;
    nat n; # Does not need to be initialized
    nat d;

    #while(1<i){
    #    n:=i;
    #    while(0<n){
    #        {d:=0}[0.5]{d:=1};
    #        i:=i-d;
    #        n:=n-1;
    #    }
    #}

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
    }

"""

post = "[i=1]"
pre = "[1<i & i<4 & phase=0] * (2/3) + [not (1<i & i<4 & phase=0)]*1"
# + Show invariant from the hurd paper!