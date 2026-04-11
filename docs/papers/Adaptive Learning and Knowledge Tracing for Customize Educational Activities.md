# Adaptive and Personalized Exercise Generation for Online Language Learning

### I. Abstract
>Adaptive learning aims to provide customized educational activities (e.g., exercises) to address individual learning needs.
 
**Cui and Sachan [1]** combine a **knowledge tracing** model that estimates each student's evolving **knowledge states** from their learning history and a **controlled** text generation model that generates exercise sentences based on each student's current estimated knowledge state and instructor requirements for desired properties. They train and evaluate their model on real-world learner interaction data from Duolingo and demonstrate that LMs guided by student states can generate **superior** exercises.

### II. Previous Approaches
- Existing methods largely *rely on* `pre-defined` questions templates or specified information sources, therby resulting in limited **knowledge coverage** and **low question** difficulty control. 
- Another line of research studies **exercise recommendation** to customize learning content based on individual capabilities and goals. However, these systems are **limited** by the diversity of the exercise pool.

To address the above limitations, they study the task of exercise generation in the context of adaptive learning, where they **hypothesize - giả thuyết** that a `student's dynamic knowledge state` holds the key to generating `adaptive` and `personalized` exercise.

### References
[1] Peng Cui and Mrinmaya Sachan. 2023. *Adaptive and Personalized Exercise Generation for Online Language Learning*. In *Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 10184-10198. Association for Computational Linguistics. https://aclanthology.org/2023.acl-long.567/
