import logging
import re

from dipper.models.assoc.Association import Assoc
from dipper.models.BiolinkVocabulary import BioLinkVocabulary as blv

__author__ = 'nlw'

LOG = logging.getLogger(__name__)
# note: currently no log issued


class G2PAssoc(Assoc):
    """
    A specific association class for defining Genotype-to-Phenotype
    relationships. This assumes that a graph is created outside of this class,
    and nodes get added.
    By default, an association will assume the "has_phenotype" relationship,
    unless otherwise specified.
    Note that genotypes are expected to be
    created and defined outside of this association,
    most likely by calling methods in the Genotype() class.

    """

    def __init__(self, graph, definedby, entity_id, phenotype_id, rel=None,
                 entity_category=blv.terms.Genotype.value,
                 phenotype_category=blv.terms.PhenotypicFeature.value):
        super().__init__(graph, definedby)
        self.entity_id = entity_id
        self.phenotype_id = phenotype_id

        if rel is None:
            rel = self.globaltt['has phenotype']

        self.start_stage_id = None
        self.end_stage_id = None
        self.environment_id = None
        self.stage_process_id = None

        self.set_subject(entity_id)
        self.set_object(phenotype_id)
        self.set_relationship(rel)

        self.entity_category = entity_category
        self.phenotype_category = phenotype_category

        return

    def set_stage(self, start_stage_id, end_stage_id):
        if start_stage_id is not None and start_stage_id.strip() != '':
            self.start_stage_id = start_stage_id
        if end_stage_id is not None and end_stage_id.strip() != '':
            self.end_stage_id = end_stage_id
        return

    def set_environment(self, environment_id):
        if environment_id is not None and environment_id.strip() != '':
            self.environment_id = environment_id

        return

    def set_association_id(self, assoc_id=None):

        if assoc_id is None:
            self.assoc_id = self.make_g2p_id()
        else:
            self.assoc_id = assoc_id

        return

    def add_association_to_graph(self, entity_category=None, phenotype_category=None):
        """
        Overrides  Association by including bnode support

        The reified relationship between a genotype (or any genotype part)
        and a phenotype is decorated with some provenance information.
        This makes the assumption that
        both the genotype and phenotype are classes.

        currently hardcoded to map the annotation to the monarch namespace
        :param g:
        :param entity_category: a biolink category CURIE for self.sub
        :param phenotype_category: a biolink category CURIE for self.obj
        :return:
        """

        if entity_category is None:
            entity_category = self.entity_category
        if phenotype_category is None:
            phenotype_category = self.phenotype_category

        Assoc.add_association_to_graph(self,
                                       subject_category=entity_category,
                                       object_category=phenotype_category)

        # make a blank stage
        if self.start_stage_id or self.end_stage_id is not None:
            stage_process_id = '-'.join((str(self.start_stage_id),
                                         str(self.end_stage_id)))
            stage_process_id = '_:'+re.sub(r':', '', stage_process_id)
            self.model.addIndividualToGraph(
                stage_process_id, None, self.globaltt['developmental_process'],
                ind_category=blv.terms.BiologicalProcess.value)

            self.graph.addTriple(
                stage_process_id, self.globaltt['starts during'], self.start_stage_id,
                subject_category=blv.terms.BiologicalProcess.value,
                object_category=blv.terms.LifeStage.value)

            self.graph.addTriple(
                stage_process_id, self.globaltt['ends during'], self.end_stage_id,
                subject_category=blv.terms.BiologicalProcess.value,
                object_category=blv.terms.LifeStage.value)

            self.stage_process_id = stage_process_id
            self.graph.addTriple(
                self.assoc_id, self.globaltt['has_qualifier'], self.stage_process_id,
                object_category=blv.terms.BiologicalProcess.value)

        if self.environment_id is not None:
            self.graph.addTriple(
                self.assoc_id, self.globaltt['has_qualifier'], self.environment_id,
                object_category=blv.terms.Environment.value)
        return

    def make_g2p_id(self):
        """
        Make an association id for phenotypic associations that is defined by:
        source of association +
        (Annot subject) +
        relationship +
        phenotype/disease +
        environment +
        start stage +
        end stage

        :return:

        """

        attributes = [self.environment_id, self.start_stage_id, self.end_stage_id]
        assoc_id = self.make_association_id(
            self.definedby, self.entity_id, self.rel, self.phenotype_id, attributes)

        return assoc_id
