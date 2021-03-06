import tensorflow as tf
tfk = tf.keras
tfkl = tfk.layers

class Edge_Update(tfkl.Layer):

    def __init__(self,
                 **kwargs):
        super(Edge_Update, self).__init__(**kwargs)
        
        self._built = False

    def build(self, input_shape):
        src_verts_shape, dst_verts_shape, edges_shape, adj_shape = input_shape

        num_src_verts = src_verts_shape[-2]
        num_dst_verts = dst_verts_shape[-2]

        d_src_vert = src_verts_shape[-1]
        d_dst_vert = dst_verts_shape[-1]
        d_edge = edges_shape[-1]

        assert num_src_verts == edges_shape[-3] \
            and num_dst_verts == edges_shape[-2]
        assert adj_shape == edges_shape[:-1]
        
        self.MLP = tfk.Sequential([
            tfkl.Dense(d_src_vert + d_dst_vert + d_edge,
                tf.nn.swish, use_bias=False),
            tfkl.Dense(d_edge, tf.nn.swish, use_bias=False)
        ])

        self._built = True

    def call(self, inputs):
        """
        params:
            inputs: tuple of tensors (src_verts, dst_verts, edges, adj)
                src_verts: tensor [..., src, val]
                dst_verts: tensor [..., dst, val]
                edges: tensor [..., src, dst, val]
                adj: tensor [..., src, dst]

        returns:
            updated edges tensor [..., src, dst, val]
        """
        src_verts, dst_verts, edges, adj = inputs

        if not self._built:
            self.build((src_verts.shape, dst_verts.shape, edges.shape, adj.shape))

        # vert-centric incoming neighbors
        vert_incoming = tf.einsum('...sd,...sv->...sdv', adj, src_verts)
        # vert_incoming: [..., src, dst, val]

        vert_outgoing = tf.einsum('...sd,...dv->...sdv', adj, dst_verts)
        # vert_outgoing: [..., src, dst, val]

        return self.MLP(tf.concat([vert_incoming, vert_outgoing, edges], axis=-1))