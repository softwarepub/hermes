# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche


import csv
from typing import Any, Callable, Union

import requests

from hermes.commands.base import HermesCommand
from hermes.model.merge.action import Concat, IdMerge, MergeAction, MergeSet
from hermes.model.types import ld_dict
from hermes.model.types.ld_context import iri_map as iri
from .base import HermesProcessPlugin


def match_equals(left: Any, right: Any) -> bool:
    """
    Compares two objects with ==.

    Args:
        left (Any): The first object for the comparison.
        right (Any): The second object for the comparison.

    Returns:
        bool: The result of the comparison.
    """
    return left == right


def match_keys(*keys: list[str], fall_back_to_equals: bool = False) -> Callable[[Any, Any], bool]:
    """
    Creates a function taking to parameters that returns true
    if both given parameter have at least one common key in the given list of keys
    and for all common keys in the given list of keys the values of both objects are the same.\n
    If fall_back_to_equals is True, the returned function returns the value of normal == comparison
    if no key from keys is in both objects.

    Args:
        keys (list[str]): The list of important keys for the comparison method.
        fall_back_to_equals (bool): Whether or not a fall back option should be used.

    Returns:
        Callable[[Any, Any], bool]: A function comparing two given objects values for the keys in keys.
    """

    # create and return the match function using the given keys
    def match_func(left: Any, right: Any) -> bool:
        """
        Compares left to right by checking if

        - they have at least one common key in a predetermined list of keys and
        - testing if both objects have equal values for all common keys in the predetermined key list.

        It may fall back on == if no common key in the predetermined list of keys exists.

        Args:
            left (Any): The first object for the comparison.
            right (Any): The second object for the comparison.

        Returns:
            bool: The result of the comparison.
        """
        if not (isinstance(left, ld_dict) and isinstance(right, ld_dict)):
            return fall_back_to_equals and (left == right)
        # create a list of all common important keys
        active_keys = [key for key in keys if key in left and key in right]
        # fall back to == if no active keys
        if fall_back_to_equals and not active_keys:
            return left == right
        # check if both objects have the same values for all active keys
        pairs = [(left[key] == right[key]) for key in active_keys]
        # return whether or not both objects had the same values for all active keys
        # and there was at least one active key
        return len(active_keys) > 0 and all(pairs)
    return match_func


def match_person(left: Any, right: Any) -> bool:
    """
    Compares two objects assuming they are representing schema:Person's
    if they are not ld_dicts, == is used as a fallback.\n
    If both objects have an @id value, the truth value returned by this function is the comparison of both ids.\n
    If either other has no @id value and both objects have at least one email value,
    they are considered equal if they have one common email.\n
    If the equality of the objects is not yet decided, == comparison of the objects is returned.

    Args:
        left (Any): The first object for the comparison.
        right (Any): The second object for the comparison.

    Returns:
        bool: The result of the comparison.
    """
    if not (isinstance(left, ld_dict) and isinstance(right, ld_dict)):
        return left == right
    if "@id" in left and "@id" in right:
        return left["@id"] == right["@id"]
    if "schema:email" in left and "schema:email" in right:
        if len(left["schema:email"]) > 0 and len(right["schema:email"]) > 0:
            mails_right = right["schema:email"]
            return any((mail in mails_right) for mail in left["schema:email"])
    return left == right


def match_multiple_types(
    *functions_for_types: list[tuple[str, Callable[[Any, Any], bool]]],
    fall_back_function: Callable[[Any, Any], bool] = match_keys("@id", fall_back_to_equals=True)
) -> Callable[[Any, Any], bool]:
    """
    Returns a function that compares two objects using the given functions.

    Args:
        functions_for_types (list[tuple[str, Callable[[Any, Any], bool]]]): Tuples of type and match_function.
            The returned function will compare two objects of a the same, given type with the specified function.
        fall_back_function (Callable[[Any, Any], bool]): The fallback for comparison if the objects that are being
            compared don't have a common type with specified compare function or at least one object
            is not a JSON-LD dictionary.

    Returns:
        Callable[[Any, Any], bool]: The function that compares the two given objects using the given functions.
    """

    # create and return the match function using the given keys
    def match_func(left: Any, right: Any) -> bool:
        """
        Compares two objects using a predetermined function if either objects is not an ld_dict
        or they don't have a common type in a predetermined list of types.\n
        If the objects are ld_dicts and have the same type with a known comparison function this is used instead.

        Args:
            left (Any): The first object for the comparison.
            right (Any): The second object for the comparison.

        :return: The result of the comparison.
        :rtype: bool
        """
        # If at least one of the objects is not an ld_dict or contains no value for the key "@type", use the fallback.
        if not (isinstance(left, ld_dict) and isinstance(right, ld_dict) and "@type" in left and "@type" in right):
            return fall_back_function(left, right)
        # Extract the list of types
        types_left = left["@type"]
        types_right = right["@type"]
        # Iterate over all known type, match_function pairs.
        # If one type is in both objects return the result of the comparison with the match_function.
        for ld_type, func in functions_for_types:
            if ld_type in types_left and ld_type in types_right:
                return func(left, right)
        # No common type with known match_function: Fallback
        return fall_back_function(left, right)
    return match_func


DEFAULT_MATCH = match_keys("@id", fall_back_to_equals=True)
""" Callable[[Any, Any], bool]: The default match function used for comparison. """

MATCH_FUNCTION_FOR_TYPE = {iri["schema:Person"]: match_person}
"""
dict[str, Callable[[Any, Any], bool]]: A dict containing for JSON_LD types the match function (not DEFAULT_MATCH).
"""

ACTIONS = {
    "default": MergeSet(DEFAULT_MATCH),
    "concat": Concat(),
    "Person": MergeSet(MATCH_FUNCTION_FOR_TYPE[iri["schema:Person"]]),
    **{
        "Or".join(types): MergeSet(match_multiple_types(
            *(("schema:" + type, MATCH_FUNCTION_FOR_TYPE.get(iri["schema:" + type], DEFAULT_MATCH)) for type in types)
        ))
        for types in [
            ("AboutPage", "CreativeWork"),
            ("AdministrativeArea", "GeoShape", "Place"),
            ("AggregateOffer", "CreativeWork", "Event", "MenuItem", "Product", "Service", "Trip"),
            ("AnatomicalStructure", "AnatomicalSystem"),
            ("AnatomicalStructure", "AnatomicalSystem", "BioChemEntity", "DefinedTerm"),
            ("AnatomicalStructure", "AnatomicalSystem", "SuperficialAnatomy"),
            ("AudioObject", "Clip", "MusicRecording"),
            ("BioChemEntity", "CreativeWork", "Event", "MedicalEntity", "Organization", "Person", "Product"),
            ("Brand", "Organization"),
            ("CategoryCode", "Thing"),
            ("Class", "Enumeration"),
            ("Class", "Enumeration", "Property"),
            ("Clip", "VideoObject"),
            ("Comment", "CreativeWork"),
            ("ContactPoint", "Place"),
            ("CreativeWork", "HowToSection", "HowToStep"),
            ("CreativeWork", "Product"),
            ("CreditCard", "MonetaryAmount", "UnitPriceSpecification"),
            ("DataFeedItem", "Thing"),
            ("Demand", "Offer"),
            ("DefinedTerm", "Enumeration", "PropertyValue", "QualitativeValue", "QuantitativeValue", "StructuredValue"),
            ("DefinedTerm", "PropertyValue"),
            ("DefinedTerm", "QuantitativeValue", "SizeSpecification"),
            ("DefinedTerm", "StructuredValue"),
            ("DefinedTerm", "Taxon"),
            ("Distance", "QuantitativeValue"),
            ("Drug", "DrugClass", "LifestyleModification", "MedicalTherapy"),
            ("Duration", "QuantitativeValue"),
            ("EducationalOrganization", "Organization"),
            ("GeoCoordinates", "GeoShape"),
            ("GeoShape", "Place"),
            ("GeospatialGeometry", "Place"),
            ("ImageObject", "Photograph"),
            ("ItemList", "ListItem", "WebContent"),
            ("ItemList", "MusicRecording"),
            ("ListItem", "Thing"),
            ("LoanOrCredit", "PaymentMethod"),
            ("Mass", "QuantitativeValue"),
            ("MedicalCondition", "PropertyValue"),
            ("MemberProgramTier", "Organization", "ProgramMembership"),
            ("MenuItem", "MenuSection"),
            ("MonetaryAmount", "MonetaryAmountDistribution"),
            ("MonetaryAmount", "PriceSpecification"),
            ("MonetaryAmount", "ShippingRateSettings"),
            ("MusicGroup", "Person"),
            ("Organization", "Person"),
            ("PerformingGroup", "Person"),
            ("Place", "PostalAddress", "VirtualLocation"),
            ("ProductGroup", "ProductModel"),
            ("Property", "PropertyValue", "StatisticalVariable"),
            ("Product", "Service"),
            ("QuantitativeValue", "ServicePeriod"),
            ("SoftwareApplication", "WebSite")
        ]
    }
}
""" dict[str, MergeAction]: A dict containing some common MergeActions. """


PROV_STRATEGY = {
    None: {
        iri["hermes-rt:graph"]: ACTIONS["concat"],
        iri["hermes-rt:replace"]: ACTIONS["concat"],
        iri["hermes-rt:reject"]: ACTIONS["concat"]
    }
}
""" dict[Literal[None], dict[str, MergeAction]]: MergeActions for provenance values. """


# Filled with entries for every schema-type that can be found inside an JSON-LD dict of type
# SoftwareSourceCode or SoftwareApplication using schema and CodeMeta as Context.
CODEMETA_STRATEGY = {None: {None: ACTIONS["default"], "@id": IdMerge()}}
""" dict[str | None, dict[str | None, MergeAction]]: MergeActions for the standard JSON_LD contexts objects. """
CODEMETA_STRATEGY[iri["schema:Thing"]] = {iri["schema:owner"]: ACTIONS["OrganizationOrPerson"]}


CODEMETA_STRATEGY[iri["schema:Action"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:agent"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:location"]: ACTIONS["PlaceOrPostalAddressOrVirtualLocation"],
    iri["schema:participant"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:provider"]: ACTIONS["OrganizationOrPerson"]
}


CODEMETA_STRATEGY[iri["schema:BioChemEntity"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:associatedDisease"]: ACTIONS["MedicalConditionOrPropertyValue"],
    iri["schema:hasMolecularFunction"]: ACTIONS["DefinedTermOrPropertyValue"],
    iri["schema:isInvolvedInBiologicalProcess"]: ACTIONS["DefinedTermOrPropertyValue"],
    iri["schema:isLocatedInSubcellularLocation"]: ACTIONS["DefinedTermOrPropertyValue"],
    iri["schema:taxonomicRange"]: ACTIONS["DefinedTermOrTaxon"]
}

CODEMETA_STRATEGY[iri["schema:Gene"]] = {
    **CODEMETA_STRATEGY[iri["schema:BioChemEntity"]],
    iri["schema:expressedIn"]: ACTIONS["AnatomicalStructureOrAnatomicalSystemOrBioChemEntityOrDefinedTerm"]
}


CODEMETA_STRATEGY[iri["schema:CreativeWork"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:accountablePerson"]: ACTIONS["Person"],
    iri["schema:audio"]: ACTIONS["AudioObjectOrClipOrMusicRecording"],
    iri["schema:author"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:character"]: ACTIONS["Person"],
    iri["schema:contributor"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:copyrightHolder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:creator"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:editor"]: ACTIONS["Person"],
    iri["schema:funder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:isBasedOn"]: ACTIONS["CreativeWorkOrProduct"],
    iri["schema:maintainer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"],
    iri["schema:producer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:provider"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:publisher"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:sdPublisher"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:size"]: ACTIONS["DefinedTermOrQuantitativeValueOrSizeSpecification"],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:translator"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:video"]: ACTIONS["ClipOrVideoObject"]
}

CODEMETA_STRATEGY[iri["schema:Article"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:NewsArticle"]] = {**CODEMETA_STRATEGY[iri["schema:Article"]]}
CODEMETA_STRATEGY[iri["schema:ScholarlyArticle"]] = {**CODEMETA_STRATEGY[iri["schema:Article"]]}
CODEMETA_STRATEGY[iri["schema:Certification"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Claim"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:claimInterpreter"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:Clip"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:actor"]: ACTIONS["PerformingGroupOrPerson"],
    iri["schema:dircetor"]: ACTIONS["Person"],
    iri["schema:musicBy"]: ACTIONS["MusicGroupOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:Comment"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:parentItem"]: ACTIONS["CommentOrCreativeWork"]
}
CODEMETA_STRATEGY[iri["schema:CorrectionComment"]] = {**CODEMETA_STRATEGY[iri["schema:Comment"]]}
CODEMETA_STRATEGY[iri["schema:CreativeWorkSeason"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:actor"]: ACTIONS["PerformingGroupOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:DataCatalog"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Dataset"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:variableMeasured"]: ACTIONS["PropertyOrPropertyValueOrStatisticalVariable"]
}
CODEMETA_STRATEGY[iri["schema:DataFeed"]] = {
    **CODEMETA_STRATEGY[iri["schema:Dataset"]],
    iri["schema:dataFeedElement"]: ACTIONS["DataFeedItemOrThing"]
}
CODEMETA_STRATEGY[iri["schema:DefinedTermSet"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:CategoryCodeSet"]] = {**CODEMETA_STRATEGY[iri["schema:DefinedTermSet"]]}
CODEMETA_STRATEGY[iri["schema:EducationalOccupationalCredential"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Episode"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:actor"]: ACTIONS["PerformingGroupOrPerson"],
    iri["schema:dircetor"]: ACTIONS["Person"],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"],
    iri["schema:musicBy"]: ACTIONS["MusicGroupOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:HowTo"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:step"]: ACTIONS["CreativeWorkOrHowToSectionOrHowToStep"]
}
CODEMETA_STRATEGY[iri["schema:HyperTocEntry"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Map"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:MediaObject"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"],
    iri["schema:height"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:ineligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:width"]: ACTIONS["DistanceOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:AudioObject"]] = {**CODEMETA_STRATEGY[iri["schema:MediaObject"]]}
CODEMETA_STRATEGY[iri["schema:DataDownload"]] = {**CODEMETA_STRATEGY[iri["schema:MediaObject"]]}
CODEMETA_STRATEGY[iri["schema:ImageObject"]] = {**CODEMETA_STRATEGY[iri["schema:MediaObject"]]}
CODEMETA_STRATEGY[iri["schema:VideoObject"]] = {
    **CODEMETA_STRATEGY[iri["schema:MediaObject"]],
    iri["schema:actor"]: ACTIONS["PerformingGroupOrPerson"],
    iri["schema:dircetor"]: ACTIONS["Person"],
    iri["schema:musicBy"]: ACTIONS["MusicGroupOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:MenuSection"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:MusicComposition"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:composer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:lyricist"]: ACTIONS["Person"]
}
CODEMETA_STRATEGY[iri["schema:MusicPlaylist"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:track"]: ACTIONS["ItemListOrMusicRecording"]
}
CODEMETA_STRATEGY[iri["schema:MusicAlbum"]] = {
    **CODEMETA_STRATEGY[iri["schema:MusicPlaylist"]],
    iri["schema:byArtist"]: ACTIONS["MusicGroupOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:MusicRelease"]] = {
    **CODEMETA_STRATEGY[iri["schema:MusicPlaylist"]],
    iri["schema:creditedTo"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:MusicRecording"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:byArtist"]: ACTIONS["MusicGroupOrPerson"],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:Photograph"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Review"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:negativeNotes"]: ACTIONS["ItemListOrListItemOrWebContent"],
    iri["schema:positiveNotes"]: ACTIONS["ItemListOrListItemOrWebContent"]
}
CODEMETA_STRATEGY[iri["schema:SoftwareApplication"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:OperatingSystem"]] = {**CODEMETA_STRATEGY[iri["schema:SoftwareApplication"]]}
CODEMETA_STRATEGY[iri["schema:RuntimePlatform"]] = {**CODEMETA_STRATEGY[iri["schema:SoftwareApplication"]]}
CODEMETA_STRATEGY[iri["schema:SoftwareSourceCode"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["maintainer"]: ACTIONS["Person"]
}
CODEMETA_STRATEGY[iri["schema:WebContent"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:WebPage"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:reviewedBy"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:AboutPage"]] = {**CODEMETA_STRATEGY[iri["schema:WebPage"]]}
CODEMETA_STRATEGY[iri["schema:WebPageElement"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:WebSite"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}


CODEMETA_STRATEGY[iri["schema:Event"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:actor"]: ACTIONS["PerformingGroupOrPerson"],
    iri["schema:attendee"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:composer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:contributor"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:dircetor"]: ACTIONS["Person"],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"],
    iri["schema:funder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:location"]: ACTIONS["PlaceOrPostalAddressOrVirtualLocation"],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"],
    iri["schema:organizer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:performer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:translator"]: ACTIONS["OrganizationOrPerson"]
}

CODEMETA_STRATEGY[iri["schema:PublicationEvent"]] = {
    **CODEMETA_STRATEGY[iri["schema:Event"]],
    iri["schema:publishedBy"]: ACTIONS["OrganizationOrPerson"]
}


CODEMETA_STRATEGY[iri["schema:Intangible"]] = {**CODEMETA_STRATEGY[iri["schema:Thing"]]}

CODEMETA_STRATEGY[iri["schema:AlignmentObject"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Audience"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Brand"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:BroadcastChannel"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:BroadcastFrequencySpecification"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Class"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:supersededBy"]: ACTIONS["ClassOrEnumeration"]
}
CODEMETA_STRATEGY[iri["schema:ComputerLanguage"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ConstraintNode"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:StatisticalVariable"]] = {**CODEMETA_STRATEGY[iri["schema:ConstraintNode"]]}
CODEMETA_STRATEGY[iri["schema:DefinedTerm"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:CategoryCode"]] = {**CODEMETA_STRATEGY[iri["schema:DefinedTerm"]]}
CODEMETA_STRATEGY[iri["schema:Demand"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:acceptedPaymentMethod"]: ACTIONS["LoanOrCreditOrPaymentMethod"],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"],
    iri["schema:eligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:ineligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:itemOffered"]: ACTIONS["AggregateOfferOrCreativeWorkOrEventOrMenuItemOrProductOrServiceOrTrip"],
    iri["schema:seller"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:EnergyConsumptionDetails"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:EntryPoint"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Enumeration"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:supersededBy"]: ACTIONS["ClassOrEnumeration"]
}
CODEMETA_STRATEGY[iri["schema:QualitativeValue"]] = {
    **CODEMETA_STRATEGY[iri["schema:Enumeration"]],
    iri[
        "schema:valueReference"
    ]: ACTIONS["DefinedTermOrEnumerationOrPropertyValueOrQualitativeValueOrQuantitativeValueOrStructuredValue"]
}
CODEMETA_STRATEGY[iri["schema:SizeSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:QualitativeValue"]]}
CODEMETA_STRATEGY[iri["schema:GeospatialGeometry"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:geoContains"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCoveredBy"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCovers"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCrosses"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoDisjoint"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoEquals"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoIntersects"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoOverlaps"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoTouches"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoWithin"]: ACTIONS["GeospatialGeometryOrPlace"]
}
CODEMETA_STRATEGY[iri["schema:Grant"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri[
        "schema:fundedItem"
    ]: ACTIONS["BioChemEntityOrCreativeWorkOrEventOrMedicalEntityOrOrganizationOrPersonOrProduct"],
    iri["schema:funder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:HealthInsurancePlan"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HealthPlanCostSharingSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HealthPlanFormulary"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HealthPlanNetwork"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ItemList"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:itemListElement"]: ACTIONS["ListItemOrThing"]
}
CODEMETA_STRATEGY[iri["schema:OfferCatalog"]] = {**CODEMETA_STRATEGY[iri["schema:ItemList"]]}
CODEMETA_STRATEGY[iri["schema:BreadcrumbList"]] = {**CODEMETA_STRATEGY[iri["schema:ItemList"]]}
CODEMETA_STRATEGY[iri["schema:Language"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ListItem"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HowToItem"]] = {**CODEMETA_STRATEGY[iri["schema:ListItem"]]}
CODEMETA_STRATEGY[iri["schema:HowToSupply"]] = {**CODEMETA_STRATEGY[iri["schema:HowToItem"]]}
CODEMETA_STRATEGY[iri["schema:HowToTool"]] = {**CODEMETA_STRATEGY[iri["schema:HowToItem"]]}
CODEMETA_STRATEGY[iri["schema:MediaSubscription"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:MemberProgram"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:MemberProgramTier"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:hasTierRequirement"]: ACTIONS["CreditCardOrMonetaryAmountOrUnitPriceSpecification"]
}
CODEMETA_STRATEGY[iri["schema:MenuItem"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:menuAddOn"]: ACTIONS["MenuItemOrMenuSection"],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"]
}
CODEMETA_STRATEGY[iri["schema:MerchantReturnPolicy"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:MerchantReturnPolicySeasonalOverride"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Occupation"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:estimatedSalary"]: ACTIONS["MonetaryAmountOrMonetaryAmountDistribution"]
}
CODEMETA_STRATEGY[iri["schema:OccupationalExperienceRequirements"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Offer"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:acceptedPaymentMethod"]: ACTIONS["LoanOrCreditOrPaymentMethod"],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"],
    iri["schema:category"]: ACTIONS["CategoryCodeOrThing"],
    iri["schema:eligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:ineligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:itemOffered"]: ACTIONS["AggregateOfferOrCreativeWorkOrEventOrMenuItemOrProductOrServiceOrTrip"],
    iri["schema:leaseLength"]: ACTIONS["DurationOrQuantitativeValue"],
    iri["schema:offeredBy"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:seller"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:AggregateOffer"]] = {
    **CODEMETA_STRATEGY[iri["schema:Offer"]],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"]
}
CODEMETA_STRATEGY[iri["schema:PaymentMethod"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ProgramMembership"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:member"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:Property"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:supersededBy"]: ACTIONS["ClassOrEnumerationOrProperty"]
}
CODEMETA_STRATEGY[iri["schema:Quantity"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Duration"]] = {**CODEMETA_STRATEGY[iri["schema:Quantity"]]}
CODEMETA_STRATEGY[iri["schema:Energy"]] = {**CODEMETA_STRATEGY[iri["schema:Quantity"]]}
CODEMETA_STRATEGY[iri["schema:Mass"]] = {**CODEMETA_STRATEGY[iri["schema:Quantity"]]}
CODEMETA_STRATEGY[iri["schema:Rating"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:author"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:AggregateRating"]] = {**CODEMETA_STRATEGY[iri["schema:Rating"]]}
CODEMETA_STRATEGY[iri["schema:Schedule"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:Series"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Service"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"],
    iri["schema:brand"]: ACTIONS["BrandOrOrganization"],
    iri["schema:broker"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:category"]: ACTIONS["CategoryCodeOrThing"],
    iri["schema:isRelatedTo"]: ACTIONS["ProductOrService"],
    iri["schema:isSimilarTo"]: ACTIONS["ProductOrService"],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"],
    iri["schema:provider"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:BroadcastService"]] = {**CODEMETA_STRATEGY[iri["schema:Service"]]}
CODEMETA_STRATEGY[iri["schema:CableOrSatelliteService"]] = {**CODEMETA_STRATEGY[iri["schema:Service"]]}
CODEMETA_STRATEGY[iri["schema:FinancialProduct"]] = {**CODEMETA_STRATEGY[iri["schema:Service"]]}
CODEMETA_STRATEGY[iri["schema:LoanOrCredit"]] = {**CODEMETA_STRATEGY[iri["schema:FinancialProduct"]]}
CODEMETA_STRATEGY[iri["schema:ServiceChannel"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:SpeakableSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:StructuredValue"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ContactPoint"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"]
}
CODEMETA_STRATEGY[iri["schema:PostalAddress"]] = {**CODEMETA_STRATEGY[iri["schema:ContactPoint"]]}
CODEMETA_STRATEGY[iri["schema:Distance"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:GeoCoordinates"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:GeoShape"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:InteractionCounter"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:interactionService"]: ACTIONS["SoftwareApplicationOrWebSite"],
    iri["schema:location"]: ACTIONS["PlaceOrPostalAddressOrVirtualLocation"]
}
CODEMETA_STRATEGY[iri["schema:MonetaryAmount"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:NutritionInformation"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:OfferShippingDetails"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:depth"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:height"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:shippingRate"]: ACTIONS["MonetaryAmountOrShippingRateSettings"],
    iri["schema:weight"]: ACTIONS["MassOrQuantitativeValue"],
    iri["schema:width"]: ACTIONS["DistanceOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:OpeningHoursSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:PostalCodeRangeSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:PriceSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:DeliveryChargeSpecification"]] = {
    **CODEMETA_STRATEGY[iri["schema:PriceSpecification"]],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"],
    iri["schema:eligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:ineligibleRegion"]: ACTIONS["GeoShapeOrPlace"]
}
CODEMETA_STRATEGY[iri["schema:UnitPriceSpecification"]] = {
    **CODEMETA_STRATEGY[iri["schema:PriceSpecification"]],
    iri["schema:billingDuration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:PropertyValue"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri[
        "schema:valueReference"
    ]: ACTIONS["DefinedTermOrEnumerationOrPropertyValueOrQualitativeValueOrQuantitativeValueOrStructuredValue"]
}
CODEMETA_STRATEGY[iri["schema:LocationFeatureSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:PropertyValue"]]}
CODEMETA_STRATEGY[iri["schema:QuantitativeValue"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri[
        "schema:valueReference"
    ]: ACTIONS["DefinedTermOrEnumerationOrPropertyValueOrQualitativeValueOrQuantitativeValueOrStructuredValue"]
}
CODEMETA_STRATEGY[iri["schema:QuantitativeValueDistribution"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:MonetaryAmountDistribution"]] = {
    **CODEMETA_STRATEGY[iri["schema:QuantitativeValueDistribution"]]
}
CODEMETA_STRATEGY[iri["schema:RepaymentSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:ServicePeriod"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:ShippingConditions"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:depth"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:height"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:shippingRate"]: ACTIONS["MonetaryAmountOrShippingRateSettings"],
    iri["schema:transitTime"]: ACTIONS["QuantitativeValueOrServicePeriod"],
    iri["schema:weight"]: ACTIONS["MassOrQuantitativeValue"],
    iri["schema:width"]: ACTIONS["DistanceOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:ShippingDeliveryTime"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:handlingTime"]: ACTIONS["QuantitativeValueOrServicePeriod"],
    iri["schema:transitTime"]: ACTIONS["QuantitativeValueOrServicePeriod"]
}
CODEMETA_STRATEGY[iri["schema:ShippingRateSettings"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:shippingRate"]: ACTIONS["MonetaryAmountOrShippingRateSettings"]
}
CODEMETA_STRATEGY[iri["schema:ShippingService"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:handlingTime"]: ACTIONS["QuantitativeValueOrServicePeriod"]
}
CODEMETA_STRATEGY[iri["schema:TypeAndQuantityNode"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:typeOfGood"]: ACTIONS["ProductOrService"]
}
CODEMETA_STRATEGY[iri["schema:WarrantyPromise"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:VirtualLocation"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}


CODEMETA_STRATEGY[iri["schema:MedicalEntity"]] = {**CODEMETA_STRATEGY[iri["schema:Thing"]]}

CODEMETA_STRATEGY[iri["schema:AnatomicalStructure"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:AnatomicalSystem"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:comprisedOf"]: ACTIONS["AnatomicalStructureOrAnatomicalSystem"]
}
CODEMETA_STRATEGY[iri["schema:DrugClass"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:LifestyleModification"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalCause"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalCondition"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:associatedAnatomy"]: ACTIONS["AnatomicalStructureOrAnatomicalSystemOrSuperficialAnatomy"],
    iri["schema:possibleTreatment"]: ACTIONS["DrugOrDrugClassOrLifestyleModificationOrMedicalTherapy"],
    iri["schema:secondaryPrevention"]: ACTIONS["DrugOrDrugClassOrLifestyleModificationOrMedicalTherapy"]
}
CODEMETA_STRATEGY[iri["schema:MedicalSignOrSymptom"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalCondition"]],
    iri["schema:possibleTreatment"]: ACTIONS["DrugOrDrugClassOrLifestyleModificationOrMedicalTherapy"]
}
CODEMETA_STRATEGY[iri["schema:MedicalSign"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalSignOrSymptom"]]}
CODEMETA_STRATEGY[iri["schema:MedicalContraindication"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalDevice"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalGuideline"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:DDxElement"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:DrugLegalStatus"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:DoseSchedule"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:DrugStrength"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:MaximumDoseSchedule"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:MedicalConditionStage"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:MedicalProcedure"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:TherapeuticProcedure"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalProcedure"]]}
CODEMETA_STRATEGY[iri["schema:MedicalTherapy"]] = {**CODEMETA_STRATEGY[iri["schema:TherapeuticProcedure"]]}
CODEMETA_STRATEGY[iri["schema:MedicalRiskFactor"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalStudy"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:MedicalTest"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:SuperficialAnatomy"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:relatedAnatomy"]: ACTIONS["AnatomicalStructureOrAnatomicalSystem"]
}


CODEMETA_STRATEGY[iri["schema:Organization"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:acceptedPaymentMethod"]: ACTIONS["LoanOrCreditOrPaymentMethod"],
    iri["schema:alumni"]: ACTIONS["Person"],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"],
    iri["schema:brand"]: ACTIONS["BrandOrOrganization"],
    iri["schema:employee"]: ACTIONS["Person"],
    iri["schema:founder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:funder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:legalRepresentative"]: ACTIONS["Person"],
    iri["schema:location"]: ACTIONS["PlaceOrPostalAddressOrVirtualLocation"],
    iri["schema:member"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:memberOf"]: ACTIONS["MemberProgramTierOrOrganizationOrProgramMembership"],
    iri["schema:ownershipFundingInfo"]: ACTIONS["AboutPageOrCreativeWork"],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"]
}

CODEMETA_STRATEGY[iri["schema:PerformingGroup"]] = {**CODEMETA_STRATEGY[iri["schema:Organization"]]}
CODEMETA_STRATEGY[iri["schema:MusicGroup"]] = {
    **CODEMETA_STRATEGY[iri["schema:PerformingGroup"]],
    iri["schema:musicGroupMember"]: ACTIONS["Person"],
    iri["schema:track"]: ACTIONS["ItemListOrMusicRecording"]
}


CODEMETA_STRATEGY[iri["schema:Person"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:alumniOf"]: ACTIONS["EducationalOrganizationOrOrganization"],
    iri["schema:brand"]: ACTIONS["BrandOrOrganization"],
    iri["schema:children"]: ACTIONS["Person"],
    iri["schema:colleague"]: ACTIONS["Person"],
    iri["schema:follows"]: ACTIONS["Person"],
    iri["schema:funder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:height"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:homeLocation"]: ACTIONS["ContactPointOrPlace"],
    iri["schema:knows"]: ACTIONS["Person"],
    iri["schema:memberOf"]: ACTIONS["MemberProgramTierOrOrganizationOrProgramMembership"],
    iri["schema:netWorth"]: ACTIONS["MonetaryAmountOrPriceSpecification"],
    iri["schema:parent"]: ACTIONS["Person"],
    iri["schema:pronouns"]: ACTIONS["DefinedTermOrStructuredValue"],
    iri["schema:relatedTo"]: ACTIONS["Person"],
    iri["schema:sibling"]: ACTIONS["Person"],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:spouse"]: ACTIONS["Person"],
    iri["schema:weight"]: ACTIONS["MassOrQuantitativeValue"],
    iri["schema:workLocation"]: ACTIONS["ContactPointOrPlace"]
}


CODEMETA_STRATEGY[iri["schema:Place"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:geo"]: ACTIONS["GeoCoordinatesOrGeoShape"],
    iri["schema:geoContains"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCoveredBy"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCovers"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCrosses"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoDisjoint"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoEquals"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoIntersects"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoOverlaps"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoTouches"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoWithin"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:photo"]: ACTIONS["ImageObjectOrPhotograph"]
}

CODEMETA_STRATEGY[iri["schema:AdministrativeArea"]] = {**CODEMETA_STRATEGY[iri["schema:Place"]]}
CODEMETA_STRATEGY[iri["schema:Country"]] = {**CODEMETA_STRATEGY[iri["schema:AdministrativeArea"]]}
CODEMETA_STRATEGY[iri["schema:CivicStructure"]] = {**CODEMETA_STRATEGY[iri["schema:Place"]]}


CODEMETA_STRATEGY[iri["schema:Product"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:brand"]: ACTIONS["BrandOrOrganization"],
    iri["schema:category"]: ACTIONS["CategoryCodeOrThing"],
    iri["schema:depth"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:height"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:isRelatedTo"]: ACTIONS["ProductOrService"],
    iri["schema:isSimilarTo"]: ACTIONS["ProductOrService"],
    iri["schema:isVariantOf"]: ACTIONS["ProductGroupOrProductModel"],
    iri["schema:negativeNotes"]: ACTIONS["ItemListOrListItemOrWebContent"],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"],
    iri["schema:positiveNotes"]: ACTIONS["ItemListOrListItemOrWebContent"],
    iri["schema:size"]: ACTIONS["DefinedTermOrQuantitativeValueOrSizeSpecification"],
    iri["schema:weight"]: ACTIONS["MassOrQuantitativeValue"],
    iri["schema:width"]: ACTIONS["DistanceOrQuantitativeValue"]
}

CODEMETA_STRATEGY[iri["schema:ProductGroup"]] = {**CODEMETA_STRATEGY[iri["schema:Product"]]}
CODEMETA_STRATEGY[iri["schema:ProductModel"]] = {
    **CODEMETA_STRATEGY[iri["schema:Product"]],
    iri["schema:isVariantOf"]: ACTIONS["ProductGroupOrProductModel"]
}


CODEMETA_STRATEGY[iri["schema:Taxon"]] = {**CODEMETA_STRATEGY[iri["schema:Thing"]]}


CODEMETA_STRATEGY[iri["schema:CreativeWorkSeries"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    **CODEMETA_STRATEGY[iri["schema:Series"]]
}

CODEMETA_STRATEGY[iri["schema:DefinedRegion"]] = {
    **CODEMETA_STRATEGY[iri["schema:Place"]],
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]]
}

CODEMETA_STRATEGY[iri["schema:Drug"]] = {
    **CODEMETA_STRATEGY[iri["schema:Product"]],
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]
}

CODEMETA_STRATEGY[iri["schema:EducationalOrganization"]] = {
    **CODEMETA_STRATEGY[iri["schema:Organization"]],
    **CODEMETA_STRATEGY[iri["schema:CivicStructure"]]
}

CODEMETA_STRATEGY[iri["schema:HowToSection"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    **CODEMETA_STRATEGY[iri["schema:ItemList"]],
    **CODEMETA_STRATEGY[iri["schema:ListItem"]]
}

CODEMETA_STRATEGY[iri["schema:HowToStep"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    **CODEMETA_STRATEGY[iri["schema:ItemList"]],
    **CODEMETA_STRATEGY[iri["schema:ListItem"]]
}

CODEMETA_STRATEGY[iri["schema:MedicalCode"]] = {
    **CODEMETA_STRATEGY[iri["schema:CategoryCode"]],
    **CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]
}

CODEMETA_STRATEGY[iri["schema:PaymentCard"]] = {
    **CODEMETA_STRATEGY[iri["schema:FinancialProduct"]],
    **CODEMETA_STRATEGY[iri["schema:PaymentMethod"]]
}
CODEMETA_STRATEGY[iri["schema:CreditCard"]] = {
    **CODEMETA_STRATEGY[iri["schema:LoanOrCredit"]],
    **CODEMETA_STRATEGY[iri["schema:PaymentCard"]]
}


class CodemetaProcessPlugin(HermesProcessPlugin):
    def __call__(self, command: HermesCommand) -> dict[Union[str, None], dict[Union[str, None], MergeAction]]:
        try:
            subtypes_for_types = CodemetaProcessPlugin.get_schema_type_hierarchy()
            strats = CodemetaProcessPlugin.get_schema_strategies(subtypes_for_types)
            strats.update(CodemetaProcessPlugin.get_codemeta_strategies(subtypes_for_types))
            strats[None] = {None: MergeSet(DEFAULT_MATCH), "@id": IdMerge()}
        except Exception:
            strats = {**CODEMETA_STRATEGY}
        for key, value in PROV_STRATEGY.items():
            strats[key] = {**value, **strats.get(key, {})}
        return strats

    @classmethod
    def get_schema_type_hierarchy(cls):
        # get and read csv file containing information on schema.org types
        # switch to schemaorg-current-https-types.csv on change of standard context in HERMES
        download = requests.get("https://schema.org/version/latest/schemaorg-current-http-types.csv")
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        # remove the first line (headers)
        type_table = list(cr)[1:]
        # build list of all subtypes for every type
        subtypes_for_types = {}
        for type_row in type_table:
            if len(type_row[7]) == 0:
                # no (direct) subtype
                subtypes_for_types[type_row[0]] = set()
            else:
                # add direct subtypes
                subtypes_for_types[type_row[0]] = set(type_row[7].split(", "))
        # only immediate subtypes have been recorded now, add sub...subtypes too
        for super_type in subtypes_for_types:
            for other_type in subtypes_for_types:
                if super_type in subtypes_for_types[other_type]:
                    subtypes_for_types[other_type].update(subtypes_for_types[super_type])
        return subtypes_for_types

    @classmethod
    def get_schema_strategies(cls, subtypes_for_types):
        # get a set of all types that have to be handled separately
        special_types = set(MATCH_FUNCTION_FOR_TYPE.keys())

        # get and read csv file containing information on schema.org properties
        # switch to schemaorg-current-https-properties.csv on change of standard context in HERMES
        download = requests.get("https://schema.org/version/latest/schemaorg-current-http-properties.csv")
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        # remove the first line (headers)
        property_table = list(cr)[1:]
        strategies = {}
        # add the strategies for all properties to all types they can occur in
        for property_row in property_table:
            # generate a set of all types this property can have values of
            shallow_range_types = set(property_row[7].split(", ")) if property_row[7] != "" else set()
            range_types = shallow_range_types.union(
                *(subtypes_for_types.get(range_type, set()) for range_type in shallow_range_types)
            )
            # get all special types this property can have values of
            special_range_types = special_types.intersection(range_types)
            # if there is a special range type this property needs a special match function
            if len(special_range_types) != 0:
                # construct the match function
                match_function = MergeSet(match_multiple_types(
                    *((range_type, MATCH_FUNCTION_FOR_TYPE[range_type]) for range_type in special_range_types),
                    fall_back_function=DEFAULT_MATCH
                ))
                # iterate over a set of all types this property can occur in
                shallow_domain_types = set(property_row[6].split(", ")) if property_row[6] != "" else set()
                for domain_type in shallow_domain_types.union(
                    *(subtypes_for_types.get(domain_type, set()) for domain_type in shallow_domain_types)
                ):
                    # add the match function to the types match functions
                    strategies.setdefault(domain_type, {})[property_row[0]] = match_function
        # return the strategies
        return strategies

    @classmethod
    def get_codemeta_strategies(cls, subtypes_for_types):
        # get a set of all types that have to be handled separately
        special_types = set(MATCH_FUNCTION_FOR_TYPE.keys())

        # FIXME: change URL on change of context to codemeta 3.0
        download = requests.get("https://raw.githubusercontent.com/codemeta/codemeta/blob/2.0/crosswalk.csv")
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        # remove the first line (headers)
        property_table = list(cr)[1:]
        strategies = {}
        for property_row in property_table:
            if property_row[0] in ("schema", ""):
                # skip empty rows
                continue
            # generate a set of all types this property can have values of
            shallow_range_types = set(iri["schema:" + range_type] for range_type in property_row[2].split(" or "))
            range_types = shallow_range_types.union(
                *(subtypes_for_types.get(range_type, set()) for range_type in shallow_range_types)
            )
            # get all special types this property can have values of
            special_range_types = special_types.intersection(range_types)
            # if there is a special range type this property needs a special match function
            if len(special_range_types) != 0:
                # construct the match function
                match_function = MergeSet(match_multiple_types(
                    *((range_type, MATCH_FUNCTION_FOR_TYPE[range_type]) for range_type in special_range_types),
                    fall_back_function=DEFAULT_MATCH
                ))
                # iterate over a set of all types this property can occur in
                shallow_domain_type = {iri[property_row[0]]}
                for domain_type in shallow_domain_type.union(subtypes_for_types.get(shallow_domain_type, set())):
                    # add the match function to the types match functions
                    strategies.setdefault(domain_type, {})[iri[property_row[1]]] = match_function
        # return the strategies
        return strategies
