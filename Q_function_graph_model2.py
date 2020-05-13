import tensorflow as tf

def Q_func(x, adj, w, p, T, initialization_stddev,
           scope, reuse=False, pre_pooling_mlp_layers = 1, post_pooling_mlp_layers = 1):
    """
    x:      B x n_vertices.
    Placeholder for the current state of the solution.
    Each row of x is a binary vector encoding
    which vertices are included in the current partial solution.
    adj:    n_vertices x n_vertices.
    A placeholder for the adjacency matrix of the graph.
    w:      n_vertices x n_vertice.
    A placeholder fot the weights matrix of the graph.
    """
    with tf.variable_scope(scope, reuse=False):
        with tf.variable_scope('thetas'):
            theta1 = tf.Variable(tf.random_normal([p], stddev=initialization_stddev), name='theta1')
            theta2 = tf.Variable(tf.random_normal([p, p], stddev=initialization_stddev), name='theta2')
            theta3 = tf.Variable(tf.random_normal([p, p], stddev=initialization_stddev), name='theta3')
            theta4 = tf.Variable(tf.random_normal([p], stddev=initialization_stddev), name='theta4')
            theta5 = tf.Variable(tf.random_normal([2 * p], stddev=initialization_stddev), name='theta5')
            theta6 = tf.Variable(tf.random_normal([p, p], stddev=initialization_stddev), name='theta6')
            theta7 = tf.Variable(tf.random_normal([p, p], stddev=initialization_stddev), name='theta7')


        with tf.variable_scope('pre_pooling_MLP', reuse=False):
            Ws_pre_pooling = []; bs_pre_pooling = []
            for i in range(pre_pooling_mlp_layers):
                Ws_pre_pooling.append(tf.Variable(tf.random_normal([p, p], stddev=initialization_stddev),
                                          name='W_MLP_pre_pooling_' + str(i)))
                bs_pre_pooling.append(tf.Variable(tf.random_normal([p], stddev=initialization_stddev),
                                          name='b_MLP_pre_pooling_' + str(i)))

            Ws_post_pooling = []; bs_post_pooling = []
            for i in range(post_pooling_mlp_layers):
                Ws_post_pooling.append(tf.Variable(tf.random_normal([p, p], stddev=initialization_stddev),
                                          name='W_MLP_post_pooling_' + str(i)))
                bs_post_pooling.append(tf.Variable(tf.random_normal([p], stddev=initialization_stddev),
                                          name='b_MLP_post_pooling_' + str(i)))

        # Define the mus
        # Loop over t
        for t in range(T):
            # First part of mu
            mu_part1 = tf.einsum('iv,k->ivk', x, theta1)

            # Second part of mu
            if t != 0:
                # Add some non linear transformation of the neighbors' embedding before pooling
                with tf.variable_scope('pre_pooling_MLP', reuse=False):
                    for i in range(pre_pooling_mlp_layers):
                        mu = tf.nn.relu(tf.einsum('kl,ivk->ivl', Ws_pre_pooling[i], mu) + bs_pre_pooling[i])

                # tf.sprase_dense_matmul(adj, mu);

                mu_part2 = tf.einsum('kl,ivk->ivl', theta2, tf.einsum('ivu,iuk->ivk', tf.sparse.to_dense(adj), mu))
                # Add some non linear transformations of the pooled neighbors' embeddings
                with tf.variable_scope('post_pooling_MLP', reuse=False):
                    for i in range(post_pooling_mlp_layers):
                        mu_part2 = tf.nn.relu(tf.einsum('kl,ivk->ivl', Ws_post_pooling[i], mu_part2) + bs_post_pooling[i])

            # Third part of mu
            mu_part3_0 = tf.einsum('ikvu->ikv', tf.nn.relu(tf.einsum('k,ivu->ikvu', theta4, tf.sparse.to_dense(w))))
            mu_part3_1 = tf.einsum('kl,ilv->ivk', theta3, mu_part3_0)

            # All all of the parts of mu and apply ReLui
            if t != 0:
                mu = tf.nn.relu(tf.add(mu_part1 + mu_part2, mu_part3_1, name='mu_' + str(t)))
            else:
                mu = tf.nn.relu(tf.add(mu_part1, mu_part3_1, name='mu_' + str(t)))

        # Define the Qs
        Q_part1 = tf.einsum('kl,ivk->ivl', theta6, tf.einsum('ivu,iuk->ivk', tf.sparse.to_dense(adj), mu))
        Q_part2 = tf.einsum('kl,ivk->ivl', theta7, mu)
        return tf.identity(tf.einsum('k,ivk->iv', theta5,
                                     tf.nn.relu(tf.concat([Q_part1, Q_part2], axis=2))),
                           name='Q')
