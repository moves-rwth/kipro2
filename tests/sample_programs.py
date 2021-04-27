
# ---------------------------------------------------------------------------------------------------------------------

# Even for 50 000 formulae, queries are super fast
geometric = """
   nat c;
   nat f;

   while(f=1){
   {f := 0}[0.5]{c := c+1}
   }
"""

#BMC Pre- and Postexpectations
geometric_post_1 = "c"
geometric_upper_1 = "c + 0.99"

geometric_test_1 = (geometric, geometric_post_1, geometric_upper_1, False)

geometric_post_2 = "c"
geometric_upper_2 = "c + 1"

geometric_test_2 = (geometric, geometric_post_2, geometric_upper_2, True)

#K-Induction Pre- and Postexpectations
geometric_k_post_1 = "c"
geometric_k_pre_1 = "[f=1]*(c+1)+[not (f=1)]*c"
geometric_k_test_1 = (geometric, geometric_k_post_1, geometric_k_pre_1, True)

geometric_k_pre_2 = "c+1"
geometric_k_test_2 = (geometric, geometric_k_post_1, geometric_k_pre_2, True)


# ---------------------------------------------------------------------------------------------------------------------

geometric_flipping = """
   nat c;
   nat f;
   nat k;

   while(f=1){
        if(k=0){
            {f := 0}[0.5]{ c := c +1 };
            k := 1
        }{
           k :=0
        }

   }
"""

#BMC Pre- and Postexpectations
geometric_flipping_post_1 = "[k=1] * c"
geometric_flipping_upper_1 = "[k=1] * (c + 0.99) + [k=0] * (c+1)"
geometric_flipping_test_1 = (geometric_flipping, geometric_flipping_post_1, geometric_flipping_upper_1, False)

geometric_flipping_post_2 = "[k=1] * c"
geometric_flipping_upper_2 = "[k=1] * (c + 0.99) + [k=0] * \\infty"
geometric_flipping_test_2 = (geometric_flipping, geometric_flipping_post_2, geometric_flipping_upper_2, False)

# ---------------------------------------------------------------------------------------------------------------------

geometric_monus = """
   nat c;
   nat f;

   while(f=1){
   {f := 0}[0.5]{ c := c - 1}
   }
"""

#BMC Pre- and Postexpectations
geometric_monus_post_1 = "c"
geometric_monus_upper_1 = "c"
geometric_monus_test_1 = (geometric_monus, geometric_monus_post_1, geometric_monus_upper_1, True)

# ---------------------------------------------------------------------------------------------------------------------

geometric_monus_2 = """
   nat c;
   nat f;

   while(f=1){
   {f := 0}[0.5]{ c := c - 1 + 2}
   }
"""

#BMC Pre- and Postexpectations
# c + 0.99 is not an upper bound on wp(c)
geometric_monus_2_test_1 = (geometric_monus_2, geometric_post_1, geometric_upper_1, False)

# Note: c+1 is not an upper bound on wp(c) since, if c=0, then c "-" 1 +2 = 2
geometric_monus_2_test_2 = (geometric_monus_2, geometric_post_2, geometric_upper_2, False)

# ---------------------------------------------------------------------------------------------------------------------

geometric_variable_step = """
   nat c;
   nat f;
   nat step;

   while(f=1){
   {f := 0}[0.5]{ c := c + step }
   }
"""


# ---------------------------------------------------------------------------------------------------------------------

dueling_cowboys_no_count = """
   # we have a variable player: player=i (i=0 or i=1) means it's player i's turn
   nat player;

   # and a variable shot: shot=0 means the current player did not shoot the opponent. shot=1 means he did
   nat shot;

   # In this model, player 0 wins with a higher probability

   while(shot=0){
      if(player = 0){
         {shot := 1}[0.6]{player := 1}
      }{
         {shot := 0}[0.4]{player := 0}
      }
   }

"""

# ---------------------------------------------------------------------------------------------------------------------

dueling_cowboys_count = """
   # we have a variable player: player=i (i=0 or i=1) means it's player i's turn
   nat player;

   # and a variable shot: shot=0 means the current player did not shoot the opponent. shot=1 means he did
   nat shot;

   nat c;

   # In this model, player 0 wins with a higher probability

   while(shot=0){
      if(player = 0){
         {shot := 1}[0.6]{player := 1}
      }{
         {shot := 1}[0.4]{player := 0}
      }

      c := c + 1
   }
"""

# ---------------------------------------------------------------------------------------------------------------------

many_dueling_cowboys_count = """
   # There are the dueling cowboys {0,...,maxPlayer}
   nat maxPlayer;

   # we have a variable player: player=i (i=0...maxPlayer) means it's player i's turn
   nat player; # Initially player <= maxPlayer

   # and a variable shot: shot=0 means the current player did not shoot the opponent. shot=1 means he did
   nat shot;

   nat c;

   while(shot=0){
      if(player = maxPlayer){
         {shot := 1}[0.1]{player := 0}
      }{
         {shot := 1}[0.1]{player := player + 1}
      }
      c := c + 1
   }
"""

# ---------------------------------------------------------------------------------------------------------------------

loop_forever = """
   while(True){skip}
"""

# ---------------------------------------------------------------------------------------------------------------------

fair_random_walk = """
   nat x;

   while((not x<=0)){
      {x := x+1 }[0.5]{ x := x-1}
   }
"""

# ---------------------------------------------------------------------------------------------------------------------

fair_random_walk_count = """
   nat x;

   nat c;  #Initially c=0

   while((not x<=0)){
      {x := x+1 }[0.5]{ x := x-1}
      c := c+1
   }
"""

# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------

unfair_random_walk = """
   nat x;

   while((not x<=0)){
      {x := x+1 }[0.1]{ x := x-1}
   }
"""

# ---------------------------------------------------------------------------------------------------------------------

# For BRP, queries become expensive very quickly

brp_simple_parameterized = """
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

#BMC Pre- and Postexpectations
brp_simple_parameterized_post_1 = "[failed = maxFailed]"
brp_simple_parameterized_upper_1 = "[failed < maxFailed & sent < toSend] * 0.8 + [not (failed < maxFailed & sent < toSend)]*\\infty"
brp_simple_parameterized_test_1 = (brp_simple_parameterized, brp_simple_parameterized_post_1, brp_simple_parameterized_upper_1, False)

brp_simple_parameterized_post_2 = "[failed = maxFailed]"
brp_simple_parameterized_upper_2 = "[failed < maxFailed & sent < toSend & (maxFailed - failed + 3 < toSend - sent)] * 0.8 + [not (failed < maxFailed & sent < toSend & (maxFailed - failed + 3 < toSend - sent))]"
brp_simple_parameterized_test_2 = (brp_simple_parameterized, brp_simple_parameterized_post_2, brp_simple_parameterized_upper_2, False)

brp_simple_parameterized_post_3 = "[failed = maxFailed]"
brp_simple_parameterized_upper_3 = "[failed < maxFailed & sent < toSend & (maxFailed - failed + 10 < toSend - sent)] * 0.8 + [not (failed < maxFailed & sent < toSend & (maxFailed - failed + 3 < toSend - sent))]"
brp_simple_parameterized_test_3 = (brp_simple_parameterized, brp_simple_parameterized_post_2, brp_simple_parameterized_upper_2, False)

#Quite interesting:
brp_simple_parameterized_post_4 = "[sent = toSend]"
brp_simple_parameterized_upper_4 = "[failed < maxFailed & sent < toSend & failed = 0 & sent=0 & (maxFailed <= toSend)] * 0.9999 + [not (failed < maxFailed & sent < toSend & failed=0 & sent=0 & (maxFailed <= toSend))]*\\infty"


#K-Induction Pre- and Postexpectations
brp_simple_parameterized_k_post_1 = "[failed=maxFailed]"
brp_simple_parameterized_k_pre_1 = "[sent = 0 & failed = 0 & failed < maxFailed & toSend <= 4] * 0.35 + [not (sent = 0 & failed = 0 & failed < maxFailed & toSend <= 4)]*1" # 5-inductive
brp_simple_parameterized_k_pre_4 = "[sent = 0 & failed = 0 & failed < maxFailed & toSend <= 4] * 0.35 + [not (sent = 0 & failed = 0 & failed < maxFailed & toSend <= 4)]*1"
brp_simple_parameterized_k_test_1 = (brp_simple_parameterized, brp_simple_parameterized_k_post_1, brp_simple_parameterized_k_pre_1, True)
brp_simple_parameterized_k_test_4 = (brp_simple_parameterized, brp_simple_parameterized_k_post_1, brp_simple_parameterized_k_pre_4, False)

brp_simple_parameterized_k_pre_2 = "[sent = 0 & failed = 0 & failed < maxFailed] * (0.35*0.4*(toSend+1)) + [not (sent = 0 & failed = 0 & failed < maxFailed)]*1"  # 7-inductive
brp_simple_parameterized_k_test_2 = (brp_simple_parameterized, brp_simple_parameterized_k_post_1, brp_simple_parameterized_k_pre_2, True)

brp_simple_parameterized_k_post_2 = "failed"
brp_simple_parameterized_k_pre_3 = "[sent < toSend & failed < maxFailed & maxFailed*5 < toSend] * (toSend*0.2) + [not (sent < toSend & failed < maxFailed & maxFailed*5 < toSend)]*\\infty"
brp_simple_parameterized_k_test_3 = (brp_simple_parameterized, brp_simple_parameterized_k_post_2, brp_simple_parameterized_k_pre_3, True)

# 3-inductive (not provable by value iteration)
post = "failed"
pre = "[failed < maxFailed & toSend<=2]*(maxFailed-0.9*0.9) + [not (failed<maxFailed & toSend<=2)]*\\infty"

# 2-inductive (not provable by value iteration)
post = "[sent=toSend]*failed"
pre = "[failed < maxFailed & sent<toSend]*(0) + [not (failed<maxFailed & sent<toSend)]*\\infty"


# 2-inductvive (not provable by value iteration)
post = "failed"
pre = "[failed < maxFailed & sent<toSend]*(maxFailed) + [not (failed<maxFailed & sent<toSend)]*\\infty"

# ---------------------------------------------------------------------------------------------------------------------

brp_simple_parameterized_count_failed = """
   # Adapted from Jip's MA
   # The number of total packages to send
   nat toSend;

   # Number of packages sent
   nat sent;

   # The maximal number of retransmission tries
   nat maxFailed;

   # The number of failed retransmission tries
   nat failed;

   # Count the total number of failed retransimissions
   nat totalFailed; # Initially totalFailed

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
         totalFailed := totalFailed +1;
      }
   }
"""

# Is 1 an upper bound on the expected number of failed retransmission tries if transmission finally succeeds?
brp_simple_parameterized_count_failed_post_1 = "[sent = toSend] * totalFailed"
brp_simple_parameterized_count_failed_upper_1 = "[failed < maxFailed & sent < toSend & totalFailed =0 & failed = 0 & sent = 0] * 1 + [not (failed < maxFailed & sent < toSend & totalFailed = 0 & failed = 0 & sent = 0)]*\\infty"

# Quite intereseting:
brp_simple_parameterized_count_failed_post_2 = "[sent = toSend]*totalFailed"
brp_simple_parameterized_count_failed_upper_2 = "[failed < maxFailed & sent < toSend & failed = 0 & sent=0 & (maxFailed <= toSend) & totalFailed = 0] * (maxFailed*0.4) + [not (failed < maxFailed & sent < toSend & failed=0 & sent=0 & (maxFailed <= toSend) & totalFailed = 0)]*\\infty"


# For the following variant, the number of formulae explodes like hell

brp_simple_parameterized_count_failed_explodes = """
    # Adapted from Jip's MA.
    # Variable free is either 0 or 1. Free=1 means hosts received answer address free. Free=1 means a collision occurred.
    # If free=0 holds on termination, then the host erroneously assumes that the address is free.
    # (inital state constraint: free=0).
    nat free;

    # answerReceived = 1 (= 0) if host does (not) receive an answer.
    nat answerReceived;

    # count keeps track of the number of times the host requested an answer.
    nat count; # Initially count=0

    nat maxCount;

    nat totalCount;

    while(count < maxCount & free = 0){
       {answerReceived := 0}[0.8]{answerReceived := 1}
       if(answerReceived=1){
         {free:=1}[0.5]{free:=0}
         totalCount:=totalCount+count
         count := 0
       }{
          count:=count+1;
       }
    }
"""

# ---------------------------------------------------------------------------------------------------------------------

complete_binary_tree = """
        nat a;
        nat b;
        nat c;
        nat maxA;
        nat maxB;

                    while (a < maxA & b < maxB) {
                        {a:=a+1} [0.5] {b := b+1}
                        c:=c+1
                    }
"""

complete_binary_tree_post_1 = "[a = maxA & b+1=a]*b"
complete_binary_tree_upper_1 = "[a<maxA & b<maxB & a=0 & b=0 & c=0]*0.9 +[not (a<maxA & b<maxB & a=0 & b=0 & c=0)]*\\infty"

#K-Induction Pre- and Postexpectations
complete_binary_tree_k_post_1 = "[a=maxA]"
complete_binary_tree_k_pre_1 = "[a<maxA & b<maxB & a=0 & b=0 & maxB<=4 & maxB < maxA]*0.94 + [not (a<maxA & b<maxB & a=0 & b=0 & maxB<=4 & maxB < maxA)]*1" # 5-inductive
complete_binary_tree_k_pre_2 = "[a<maxA & b<maxB & maxB<=4 & maxB < maxA]*0.94 + [not (a<maxA & b<maxB & maxB<=4 & maxB < maxA)]*1" # 5-inductive

complete_binary_tree_k_post_2 = "a"
complete_binary_tree_k_pre_3 = "[a < maxA & b < maxB]*maxA + [not (a < maxA & b < maxB)]*\\infty" #2-inductive

complete_binary_tree_k_post_3 = "a"
complete_binary_tree_k_pre_4 = "[a < maxA & b < maxB & (not (b+2 < maxB)) & a+2<maxA] * (maxA - (b + 0.25*maxB)) + [not (a < maxA & b < maxB & (not (b+2 < maxB)) & a+2<maxA)]*\\infty"

# ---------------------------------------------------------------------------------------------------------------------

zero_conf_parameterized = """
    # Adapted from Jip's MA.
    # Variable free is either 0 or 1. Free=1 means hosts received answer address free. Free=1 means a collision occurred.
    # If free=0 holds on termination, then the host erroneously assumes that the address is free.
    # (inital state constraint: free=0).
    nat free;

    # answerReceived = 1 (= 0) if host does (not) receive an answer.
    nat answerReceived;

    # count keeps track of the number of times the host requested an answer.
    # (initial state constraint: count = 0)
    nat count;

    nat maxCount;

    nat totalCount;

    while(count < maxCount & free = 0){
       {answerReceived := 0}[0.8]{answerReceived := 1}
       if(answerReceived=1){
         {free:=1}[0.5]{free:=0}
         count := 0
       }{
          count:=count+1;
          totalCount:=totalCount+1
       }
    }
"""

#BMC Pre- and Postexpectations
zero_conf_parameterized_post_1 = "[free = 0]*totalCount"
#with 5, we get getting to unrolling depth 24 already takes very long
zero_conf_parameterized_upper_1 = "[count < maxCount & free=0 & totalCount = 0]*2 +[not (count < maxCount & free=0 & totalCount = 0)]*\\infty"

zero_conf_parameterized_post_2 = "a"
zero_conf_parameterized_pre_2 = "[a < maxA & b < maxB & (not (b+2 < maxB)) & a+2<maxA] * (maxA - (b + 0.25*maxB)) + [not (a < maxA & b < maxB & (not (b+2 < maxB)) & a+2<maxA)]*\\infty"


# ---------------------------------------------------------------------------------------------------------------------
zero_conf_parameterized_totalcount = """
    # Adapted from Jip's MA.
    # Variable free is either 0 or 1. Free=1 means hosts received answer address free. Free=1 means a collision occurred.
    # If free=0 holds on termination, then the host erroneously assumes that the address is free.
    # (inital state constraint: free=0).
    nat free;

    # answerReceived = 1 (= 0) if host does (not) receive an answer.
    nat answerReceived;

    # count keeps track of the number of times the host requested an answer.
    # (initial state constraint: count = 0)
    nat count;

    nat maxCount;

    nat totalCount;

    while(count < maxCount & free = 0){
       {answerReceived := 0}[0.8]{answerReceived := 1}
       if(answerReceived=1){
         {free:=1}[0.5]{free:=0}
         count := 0
       }{
          count:=count+1;
          totalCount:=totalCount+1
       }
    }
"""

# BMC Pre- and Postexpectations
zero_conf_parameterized_totalcountpost_1 = "[free = 0]*totalCount"
# with 5, this works, too
zero_conf_parameterized_totalcount_upper_1 = "[count < maxCount & free=0 & totalCount = 0]*2 +[not (count < maxCount & free=0 & totalCount = 0)]*\\infty"

# Further programs: load/unload, grids, crowds, mutual exclusion protocols

# ---------------------------------------------------------------------------------------------------------------------


# An example where we get a really high unrolling depth
chain = """
 nat c;
 nat f;
 nat N;

 while(c<N & f=0){
    {f:=1}[0.01]{c:=c+1}
 }
"""

chain_post_1 = "[f=1]"
chain_upper_1 = "[c<N & c=0 & f=0]*0.5 + [not (c<N & c=0 & f=0)]*\\infty"

chain_post_2 = "[f=1]*c"
chain_upper_2   = "[c<N & c=0 & f=0]*(0.25*N) + [not (c<N & c=0 & f=0)]*\\infty"


# ---------------------------------------------------------------------------------------------------------------------

# Idea: Try to verify that for every e1,e2 with e1+5=e2 we have Prob(result=k) = 1/5 for all k \in {e1+1,...,e1+5=e2}
# Bug: l=0 unreachable (provable by k-induction)
random_number_generator_original = """
    # Adapted from from https://arxiv.org/pdf/1802.10467.pdf (QSL), pp.115f .
    # We model uniform(0, l), i.e., uniformly sample a number between 0 and
    nat l;

    nat x;
    nat i;
    nat j;
    nat y;
    nat r; # Initially r=l+1 to ensure rejection sampling in case r is not set in the last phase

    nat phase; # Initially 0

    while(not (r<=l)) { # Rejection sampling
        if(phase = 0){
           # Initialization
           x:=0;
           i:=0;
           y:=1;
           j:=0;
           phase:=1;

        }{
           if(phase = 1){ # Generate l random bits in x
                if(i<l){ # Guard satisfied?
                   i := i+1;
                   x:=2*x;
                   {skip}[0.5]{x:=x+1}
                }{ # Enter phase 2
                   phase := 2
                }
           }{
              if(phase=2){ # Check whether x is a power of two
                 if(y<x & j<l){ # guard satisfied?
                    j:=j+1;
                    y:=2*y;
                 }{
                    if(y=x){ # Position found
                        r:=j
                    }{ # Restart
                        phase:=0
                    }
                 }
              }{skip}
           }
        }
    }



"""

#post_expectation = "[r=0]"
    #upper_bound_expectation = "[phase=0 & l=0 & r=1]*0 + [not (phase=0 & l=0 & r=1)]*1"
    #is k-inductive since there is a bug in the random number generator

    #post_expectation = "[r=1]"
    #upper_bound_expectation = "[phase=0 & l=1 & r=2]*0 + [not (phase=0 & l=1 & r=2)]*1"

    # Is 7-inductive!!
    #post_expectation = "[r=2]"
    #upper_bound_expectation = "[phase=0 & l=2 & r=3]*0.5 + [not (phase=0 & l=2 & r=3)]*1" # TODO: Test whether 0.25 is provable (should not be the case)

    #post_expectation = "[r=3]"
    #upper_bound_expectation = "[phase=0 & l=3 & r=4]*0.4 + [not (phase=0 & l=3 & r=4)]*1"


# Idea: Try to verify that for every e1,e2 with e1+5=e2 we have Prob(result=k) = 1/5 for all k \in {e1+1,...,e1+5=e2}
# STill buggy!!
random_number_generator_still_buggy = """
    # Adapted from from https://arxiv.org/pdf/1802.10467.pdf (QSL), pp.115f .
    # We model uniform(0, l), i.e., uniformly sample a number between 0 and
    nat l;

    nat x;
    nat i;
    nat j;
    nat y;
    nat r; # Initially l+1 to ensure rejection sampling in case r is not set in the last phase

    nat phase; # Initially 0

    while(not (r<=l)) { # Rejection sampling
        if(phase = 0){
           # Initialization
           x:=0;
           i:=0;
           y:=1;
           j:=0; # Does this need to be fixed to j=1? Think about special case l=1! What if l != 1
           phase:=1;

        }{
           if(phase = 1){ # Generate l random bits in x
                if(i<l){ # Guard satisfied?
                   i := i+1;
                   x:=2*x;
                   {skip}[0.5]{x:=x+1}
                }{ # Enter phase 2
                   phase := 2
                }
           }{
              if(phase=2){ # Check whether x is a power of two
                 if(y<x & j<l){ # guard satisfied?
                    j:=j+1;
                    y:=2*y;
                 }{
                    if(y=x){ # Position found
                        r:=j
                    }{
                        # Restart
                        phase:=0
                    }
                 }
              }{skip}
           }
        }
    }

"""


# ---------------------------------------------------------------------------------------------------------------------

# We can verify this for fixed n

random_number_generator_from_ba = """
# Adapted form http://www-i2.informatik.rwth-aachen.de/pub/index.php?type=download&pub_id=1233, which in turn adapted from
# Jérémie Lumbroso. Optimal Discrete Uniform Generation from Coin Flips, and Applications.
# In: CoRR abs/1304.1916 (2013).

# We want to model uniform(0,...,n-1)
nat n; #Should be >=0, since it denotes the size of the list we sample from
nat v; # Initially 1
nat c; # Initially 0; the result
nat running; # Initially 0

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
}


"""


# This is the infinite-state version of the above:

random_number_generator_from_ba_array = """
# Adapted form http://www-i2.informatik.rwth-aachen.de/pub/index.php?type=download&pub_id=1233, which in turn adapted from
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
}
"""

# Cool. This is 3-inductive: And not provable by VI!
random_number_generator_from_ba_array_post_1 = "[c=i]"
random_number_generator_from_ba_array_pre_1 = "[elow+2=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh)]*0.4 + [not (elow+2=ehigh & n=ehigh-elow+1 & v=1 & c=0 & running=0 & (not (i < elow)) & (i <= ehigh))]*1"



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
}
"""

random_number_post_1 = "[c=i]"
random_number_pre_1 = "[n=2 & v=1 & c=0 & running=0]*1/2 + [not (n=2 & v=1 & c=0 & running=0)]*1"



# Further programs and invariants from
# Adapted form http://www-i2.informatik.rwth-aachen.de/pub/index.php?type=download&pub_id=1233, which in turn adapted from

geo2 = """
    nat x;
    nat y;
    nat z;

    while(not (z=0)){
       y:=y+1;
       {z:=0}[1/4]{x:=x+y}
    }

"""

bin1 = """
    nat x;
    nat y;

    while(0 <= n-1){
       {x:=x+1}[1/4]{skip}
       n:=n-1
    }
"""

# ---------------------------------------------------------------------------------------------------------------------
# The following is adapted from
#Joe Hurd, Annabelle McIver, Carroll Morgan:
#Probabilistic Guarded Commands Mechanized in HOL. Electron. Notes Theor. Comput. Sci. 112: 95-111 (2005)

rabin_mutual_exclusion = """

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

# Hurd, McIver, and Morgan prove:
# [i=1] + [1 < i]*2/3  <= wlp[i=1]

# The following is 5-inductive
rabin_mutual_exclusion_post_1 = "[i=1]"
rabin_mutual_exclusion_pre_1 = "[1<i & i<3 & phase=0] * (0.67) + [not (1<i & i<3 & phase=0)]*1"


# ---------------------------------------------------------------------------------------------------------------------
# From Joe Hurd's dissertation:
# https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-566.pdf


# Further ideas: Rejection sampling? +  tortoise and hare


# Two geometric loops in sequence
two_geometric_in_sequence = """

    nat x1;
    nat x2;
    nat coin;
    nat phase; # Initially 0
    nat terminate; #initially 0
    nat result;

   while(terminate=0){
       if(phase=0){
          # Sample x1 from Geom(1/2)
          coin:=1
          phase:=1
       }{
          if(phase=1){
             if(coin=1){
                {coin:=0}[1/2]{x1:=x1+1}
             }{
                # Sample loop terminated
                coin:=1
                phase:=2
             }
          }{
             if(phase=2){
                if(coin=1){
                   {coin:=0}[1/2]{x2:=x2+1}
                }{
                  #Sample loop terminated. Add up x1 and x2 and terminate
                  result:=x1+x2;
                  terminate:=1;
                }
             }{
              skip
             }
          }
       }
   }
"""

#3-inductive
post = "result"
pre = "[terminate=0 & phase=2]*(x1+x2+1) + [terminate=0 & phase=1]*(x1+x2+2) + [terminate=0 & phase=0]*(x1+x2+2) + [not (terminate=0 & (phase=2 || phase=1 || phase=0))]*\\infty"


# Taken from: The Probabilistic
# Chomsky-Schützenberger Hierarchy

one_over_pi = """
    nat x1;
    nat x2;
    nat coin;
    nat t;
    nat phase; # initially 0

    while(...){
       if(phase=0){
          # x1 is set to Geom(1/4)
          coin:=1;
          phase:=1;
       }{
          if(phase=1){
             #x1 is set to Geom(1/4)
             if(coin=1){
                {coin:=0}[1/4]{x1:=x1+1}
             }{
                phase:=2
             }
          }{
             if(phase=2){
                #2 is set to Geom(1/4)
                coin:=1
                phase:=3
             }{
                if(phase=3){
                   if(coin=1){
                      {coin:=0}[1/4]{x1:=x1+1}
                    }{
                       phase:=4
                    }
                }{
                   if(phase=4){
                      t:=x1+x2
                   }{
                      skip
                   }
                }
             }
          }

       }

    }




"""


# The following is adapted from: Aleksandar Chakarov, Sriram Sankaranarayanan, Probabilistic program analysis with martingales (CAV 2013)
# Tortoise and hare:

# Not successful so far
tortoise_hare = """

    nat h; # Initially 0
    nat t; # Initially 30
    nat jump;
    nat tick;

    while( h<=t ){
        {jump := unif(0,10); h:=h+jump;}[0.5]{}
        t:=t+1;
        tick:=tick+1;
    }
"""

post = "tick"
pre = "(t+9-h + tick)"



# The following are adapted from
# Van Chan Ngo, Quentin Carbonneaux, Jan Hoffmann:
# Bounded expectations: resource analysis for probabilistic programs. PLDI 2018: 496-512


ber = """
 nat x;
 nat n;
 nat tick;

 while(x<n){
  {x:=x+1}[0.5]{x:=x+2};
  tick:=tick+1;
 }
"""

post = "tick"
pre = "((n-x) + tick)"





# Hoffmann derives upper bound 0.5*(x+2) + 0.5*(y+2)
c4bt30 = """
   nat x;
   nat y;
   nat t;
   nat z;

   nat help;
   nat count;

   while( not (x <= 0) ){
       help := unif(1,3);
       x:=x-help;
       t:=x;
       x=y;
       y=t;
       count:=count+1;
   }

"""


# Example where preprocessing (=reduce number Summation Normal Form objects) is highly beneficial
roulette = """
    nat money; # Initially 10
    nat n;
    nat z;
    nat help;
    nat coin;
    nat count;

    while(n <= money){
        # Bank lost
        {coin:=1}[36/37]{coin:=0}
        if(coin = 1){

            {coin:=1}[1/3]{coin:=0}
            if(coin=1){

               {coin:=1}[1/2]{coin:=0}
               if(coin=1){
                    help := unif(3,6);
                    money := money + help;
               }{
                  help := unif(1,2);
                  money := money + help;
               }

            }{

               {coin:=1}[1/2]{coin:=0}
               if(coin=1){

                  {coin:=1}[1/3]{coin:=0}
                  if(coin=1){
                     help := unif(3,6);
                     money := money + help;
                  }{
                     help := unif(1,2);
                     money := money + help;
                  }

               }{
                  {coin:=1}[2/3]{coin:=0}
                  if(coin=1){
                     help := unif(3,6);
                     money := money - help;
                  }{
                     help := unif(5,10);
                     money := money - help;
                  }
               }

            }

        }{
           help := unif(5,10)
           money := money - help
        }
        count := count + 1;
    } """


#Benchmark is called rdbub
randomized_insertion_sort = """

// examples/NCH-18/polynomial/rdbub.imp
nat m;
nat n;
nat r;
nat ticks;
while (0 < n) {
    r := 0 : 1/2 + 1 : 1/2;
    n := n - r;
    m := n;
    while (0 < m) {
        { m := m - 1; } [1/3] {
            skip;
        }
        ticks := ticks + 1;
    }
}
"""





# Examples from Jinyi Wang, Yican Sun, Hongfei Fu, Amir Kafshdar Goharshady, Krishnendu Chatterjee:
# Quantitative Analysis of Assertion Violations in Probabilistic Programs. CoRR abs/2011.14617 (2020)

coupon_5 = """

    nat i; # Number of coupons collected so far
    nat t; # Number of draws
    nat coin;

    while(i <= 5){

        if(i=0){
           i:=i+1
           t:=t+1
        }

        if(i=1){
           {coin:=1}[0.8]{coin:=0}
           if(coin=1){
              i:=i+1
              t:=t+1
           }{
              t:=t+1
           }
        }

        if(i=2){
           {coin:=1}[0.6]{coin:=0}
           if(coin=1){
              i:=i+1
              t:=t+1
           }{
              t:=t+1
           }
        }

        if(i=3){
           {coin:=1}[0.4]{coin:=0}
           if(coin=1){
              i:=i+1
              t:=t+1
           }{
              t:=t+1
           }
        }

        if(i=4){
           {coin:=1}[0.2]{coin:=0}
           if(coin=1){
              i:=i+1
              t:=t+1
           }{
              t:=t+1
           }
        }
    }

"""



programs = [geometric, geometric_flipping, dueling_cowboys_no_count, dueling_cowboys_count, loop_forever,
            fair_random_walk, unfair_random_walk, brp_simple_parameterized, complete_binary_tree]

