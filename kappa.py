def multirater_kfree(n_ij, n, k):
    '''
    Computes Randolph's free marginal multirater kappa for assessing the 
    reliability of agreement between annotators.
    
    Args:
        n_ij: An N x k array of ratings, where n_ij[i][j] annotators 
              assigned case i to category j.
        n:    Number of raters.
        k:    Number of categories.
    Returns:
        Percentage of overall agreement and free-marginal kappa
    
    See also:
        http://justusrandolph.net/kappa/
    '''
    N = len(n_ij)
    
    P_e = 1./k
    P_O = (
        1./(N*n*(n-1))
        * 
        (sum(n_ij[i][j]**2 for i in range(N) for j in range(k)) - N*n)
    )
    
    kfree = (P_O - P_e)/(1 - P_e)
    
    return P_O, kfree
