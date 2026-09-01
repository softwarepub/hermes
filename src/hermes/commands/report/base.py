# SPDX-FileCopyrightText: 2026 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Fritzsche

import argparse
from typing_extensions import Self

from pydantic import BaseModel

from hermes.commands.base import HermesCommand
from hermes.model.hermes_cache import HermesCacheManager
from hermes.model.provenance.ld_prov import ld_prov_list


class HermesReportSettings(BaseModel):
    """ Configuration of the ``report`` command. """
    pass


class HermesReportCommand(HermesCommand):
    """
    Generate a summarized provenance report for the steps chosen by the user.

    Attributes:
        command_name (str): (class attribute) The name of the command.
        settings_class (type): (class attribute) The settings class for general report settings.
    """

    command_name: str = "report"
    settings_class: type = HermesReportSettings

    def init_command_parser(self: Self, command_parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for report command.

        Args:
            command_parser (ArgumentParser): The used argument parser.

        Returns:
            None:
        """
        command_parser.add_argument(
            "--steps",
            nargs="*",
            default=["harvest", "process", "curate", "deposit", "postprocess"],
            choices=["harvest", "process", "curate", "deposit", "postprocess"],
            help="Steps for which the report should be generated. Default is every step."
        )

    def __call__(self: Self, args: argparse.Namespace) -> None:
        """
        Execute the hermes command `self`.

        Args:
            args (Namespace): The namespace that was returned by the command line parser when reading the arguments.

        Returns:
            None:
        """
        print("\nProvenance report for HERMES:")
        # print the report for every step
        for step in args.steps:
            # reset ld_prov_list because it is usually a singelton
            ld_prov_list.INDICES = {}
            # print the report
            match step:
                case "harvest":
                    self.report_harvest()
                case "process":
                    self.report_process()
                case "curate":
                    self.report_curate()
                case "deposit":
                    self.report_deposit()
                case "postprocess":
                    self.report_postprocess()
        print("")

    def report_harvest(self: Self) -> None:
        """
        Print the report for the harvest step.

        Returns:
            None:
        """
        print("- Harvest:")
        # load provenance data or error out
        ctx = HermesCacheManager()
        ctx.prepare_step("harvest")
        with ctx["provenance"] as cache:
            try:
                prov_doc = ld_prov_list.load_ld_prov_list(cache["result"])
            except KeyError:
                print("No provenance data has been recorded so far.")
                return
            finally:
                ctx.finalize_step("harvest")
        # get basic hermes objects
        harvest_base_plugin = prov_doc.get_hermes_base_plugin("harvest")
        harvest_command = prov_doc.get_hermes_command("harvest")
        hermes_cache = prov_doc.get_hermes_cache()
        plugins = prov_doc.shallow_search(lambda node: (
            "prov:actedOnBehalfOf" in node and node["prov:actedOnBehalfOf"] == [harvest_base_plugin.ref]
        ))
        # for every plugin print the info on this plugins execution
        for plugin in plugins:
            # print basic info on the plugin
            print(
                f"  - Plugin {plugin['@id'][24:]} ({plugin['schema:name'][0]}, version "
                f"{vers if (vers := plugin.get('schema:softwareVersion', False)) else 'N/A'})"
            )
            # print every source loaded by the plugin
            print("    - Loaded data from:")
            for load_action in prov_doc.shallow_search(lambda node: (
                "prov:wasAssociatedWith" in node and
                node["prov:wasAssociatedWith"] == [harvest_base_plugin.ref, plugin.ref]
            )):
                id_of_source = load_action["prov:used"][0]["@id"]
                source = prov_doc.shallow_search(lambda node: ("@id" in node and node["@id"] == id_of_source))[0]
                print(
                    f"      - {source['schema:url'][0]} (at {load_action['prov:startedAtTime'][0]}, took " +
                    f"{load_action['prov:endedAtTime'][0]-load_action['prov:startedAtTime'][0]})"
                )
            # print infos on the result
            store_action = prov_doc.shallow_search(lambda node: (
                "prov:wasAssociatedWith" in node and
                node["prov:wasAssociatedWith"] == [plugin.ref, hermes_cache.ref, harvest_command.ref]
            ))[0]
            print(
                f"    - Results stored (at {store_action['prov:startedAtTime'][0]}, took "
                f"{store_action['prov:endedAtTime'][0]-store_action['prov:startedAtTime'][0]}) in:"
            )
            for result in prov_doc.shallow_search(lambda node: (
                "prov:wasGeneratedBy" in node and node["prov:wasGeneratedBy"] == [store_action.ref]
            )):
                print(f"      - {result['schema:url'][0]} ({result['schema:description'][0].split(' ')[1]})")

    def report_process(self: Self) -> None:
        """
        Print the report for the process step.

        Returns:
            None:
        """
        print("- Process:")
        # load provenance data or error out
        ctx = HermesCacheManager()
        ctx.prepare_step("process")
        with ctx["provenance"] as cache:
            try:
                prov_doc = ld_prov_list.load_ld_prov_list(cache["result"])
            except KeyError:
                print("No provenance data has been recorded so far.")
                return
            finally:
                ctx.finalize_step("process")
        # get basic hermes objects
        process_base_plugin = prov_doc.get_hermes_base_plugin("process")
        process_command = prov_doc.get_hermes_command("process")
        hermes_cache = prov_doc.get_hermes_cache()
        plugins = prov_doc.shallow_search(lambda node: (
            "prov:actedOnBehalfOf" in node and node["prov:actedOnBehalfOf"] == [process_base_plugin.ref]
        ))
        # print info on all plugins and their strategy generation
        for plugin in plugins:
            print(
                f"  - Plugin {plugin['@id'][24:]} ({plugin['schema:name'][0]}, version "
                f"{vers if (vers := plugin.get('schema:softwareVersion', False)) else 'N/A'}):"
            )
            strategy_generation = prov_doc.shallow_search(lambda node: (
                "prov:wasAssociatedWith" in node and node["prov:wasAssociatedWith"] == [plugin.ref]
            ))[0]
            print(
                f"    - Generated strategies at {strategy_generation['prov:startedAtTime'][0]} took "
                f"{strategy_generation['prov:endedAtTime'][0]-strategy_generation['prov:startedAtTime'][0]}"
            )
        load_actions = prov_doc.shallow_search(lambda node: (
            "prov:wasAssociatedWith" in node and
            node["prov:wasAssociatedWith"] == [hermes_cache.ref, process_command.ref] and
            "prov:used" in node and
            len(node["prov:used"]) == 3
        ))
        # print info on the data loaded that was merged
        for index, load_action in enumerate(sorted(load_actions, key=lambda it: it["prov:startedAtTime"][0]), start=1):
            print(
                f"  - In load {index} loaded (at {load_action['prov:startedAtTime'][0]}, took"
                f" {load_action['prov:endedAtTime'][0]-load_action['prov:startedAtTime'][0]}"
                ", may have been overwritten) from:"
            )
            loaded = [item["@id"] for item in load_action["prov:used"]]
            sources = prov_doc.shallow_search(lambda node: ("@id" in node and node["@id"] in loaded))
            for source in sources:
                print(f"    - {source['schema:url'][0]}")
        bigest_mergers = prov_doc.shallow_search(lambda node: (
            "prov:wasAssociatedWith" in node and
            node["prov:wasAssociatedWith"] == [process_command.ref] and
            "prov:wasInformedBy" in node and
            len(node["prov:wasInformedBy"]) == 3
        ))
        # print info on the merges
        for index, merger in enumerate(sorted(bigest_mergers, key=lambda it: it["prov:startedAtTime"][0]), start=1):
            if index == 1:
                merged = "merged data from load 1 with data of load 2"
            else:
                merged = f"merged data from load {index + 1} with old results"
            print(
                f"  - Merge {index} {merged} at {merger['prov:startedAtTime'][0]} took "
                f"{merger['prov:endedAtTime'][0]-merger['prov:startedAtTime'][0]}"
            )
        write_action = prov_doc.shallow_search(lambda node: (
            "prov:wasAssociatedWith" in node and
            node["prov:wasAssociatedWith"] == [hermes_cache.ref, process_command.ref] and
            "prov:used" in node and
            len(node["prov:used"]) == 1
        ))[0]
        stored_objects = prov_doc.shallow_search(lambda node: (
            "prov:wasGeneratedBy" in node and node["prov:wasGeneratedBy"] == [write_action.ref]
        ))
        # print info on the stored data
        print(
            f"  - Results stored (at {write_action['prov:startedAtTime'][0]} took "
            f"{write_action['prov:endedAtTime'][0]-write_action['prov:startedAtTime'][0]}) in:"
        )
        for res in stored_objects:
            print(f"    - {res['schema:url'][0]} ({res['schema:description'][0].split(' ')[1]})")

    def report_curate(self: Self) -> None:
        """
        Print the report for the curate step.

        Returns:
            None:
        """
        print("- Curate:")
        # load provenance data or error out
        ctx = HermesContext()
        ctx.prepare_step("curate")
        with ctx["provenance"] as cache:
            try:
                prov_doc = ld_prov_list.load_ld_prov_list(cache["result"])
            except KeyError:
                print("No provenance data has been recorded so far.")
                return
            finally:
                ctx.finalize_step("curate")
        # get basic hermes objects
        curate_base_plugin = prov_doc.get_hermes_base_plugin("curate")
        process_command = prov_doc.get_hermes_command("process")
        hermes_cache = prov_doc.get_hermes_cache()
        # print info on the used plugin
        curate_plugin = prov_doc.shallow_search(lambda node: (
            "prov:actedOnBehalfOf" in node and node["prov:actedOnBehalfOf"] == [curate_base_plugin.ref]
        ))[0]
        print(
            f"  - Plugin used:\n    - {curate_plugin['@id'][23:]} ({curate_plugin['schema:name'][0]}, version "
            f"{vers if (vers := curate_plugin.get('schema:softwareVersion', False)) else 'N/A'})"
        )
        # get objects that contain info on the curation
        store_action_of_process = prov_doc.shallow_search(lambda node: (
            "prov:wasAssociatedWith" in node and
            node["prov:wasAssociatedWith"] == [process_command.ref, hermes_cache.ref] and
            "prov:wasInformedBy" in node
        ))[0]
        stored_results_of_process = prov_doc.shallow_search(lambda node: (
            "prov:wasGeneratedBy" in node and node["prov:wasGeneratedBy"] == [store_action_of_process.ref]
        ))
        load_action = prov_doc.shallow_search(lambda node: (
            "prov:used" in node and node["prov:used"] == [res.ref for res in stored_results_of_process]
        ))[0]
        curate_activity = prov_doc.shallow_search(lambda node: (
            "prov:wasInfluencedBy" in node and node["prov:wasInfluencedBy"] == [curate_plugin.ref]
        ))[0]
        results = prov_doc.shallow_search(lambda node: (
            "prov:wasDerivedFrom" in node and node["prov:wasDerivedFrom"] == [curate_activity.ref]
        ))
        write = prov_doc.shallow_search(lambda node: (
            "prov:used" in node and node["prov:used"] == [curate_activity.ref]
        ))[0]
        # print curation info
        print(
            f"  - Time consumed:\n    - Curation at ~{load_action['prov:endedAtTime'][0]} took"
            f" ~{curate_activity['prov:generatedAtTime'][0]-load_action['prov:endedAtTime'][0]}"
        )
        print(
            f"  - Uncurated metadata loaded (at {load_action['prov:startedAtTime'][0]}"
            f", took {load_action['prov:endedAtTime'][0]-load_action['prov:startedAtTime'][0]}"
            ", may have been overwritten) from:"
        )
        for source in stored_results_of_process:
            print(4*" " + f"- {source['schema:url'][0]} ({source['schema:description'][0].split(' ')[1]})")
        print(
            f"  - Curated metadata stored (at {write['prov:startedAtTime'][0]}, took "
            f"{write['prov:endedAtTime'][0]-write['prov:startedAtTime'][0]}) in:"
        )
        for result in results:
            print(f"    - {result['schema:url'][0]} ({result['schema:description'][0].split(' ')[1]})")

    def report_deposit(self: Self) -> None:
        """
        Print the report for the deposit step.

        Returns:
            None:
        """
        print("- Deposit:")
        # load provenance data or error out
        ctx = HermesContext()
        ctx.prepare_step("deposit")
        with ctx["provenance"] as cache:
            try:
                prov_doc = ld_prov_list.load_ld_prov_list(cache["result"])
            except KeyError:
                print("No provenance data has been recorded so far.")
                return
            finally:
                ctx.finalize_step("deposit")
        # get basic hermes objects
        deposit_base_plugin = prov_doc.get_hermes_base_plugin("deposit")
        curate_command = prov_doc.get_hermes_command("curate")
        hermes_cache = prov_doc.get_hermes_cache()
        # print info on the plugin
        deposit_plugin = prov_doc.shallow_search(lambda node: (
            "prov:actedOnBehalfOf" in node and node["prov:actedOnBehalfOf"] == [deposit_base_plugin.ref]
        ))[0]
        print(
            f"  - Plugin used:\n    - {deposit_plugin['@id'][24:]} ({deposit_plugin['schema:name'][0]}, version "
            f"{vers if (vers := deposit_plugin.get('schema:softwareVersion', False)) else 'N/A'})"
        )
        # get objects containing info on map and update of the metadata
        store_action_of_curate = prov_doc.shallow_search(lambda node: (
            "prov:wasAssociatedWith" in node and
            node["prov:wasAssociatedWith"] == [curate_command.ref, hermes_cache.ref] and
            "prov:used" in node and
            len(node["prov:used"]) == 1
        ))[0]
        stored_results_of_curate = prov_doc.shallow_search(lambda node: (
            "prov:wasGeneratedBy" in node and node["prov:wasGeneratedBy"] == [store_action_of_curate.ref]
        ))
        load_action = prov_doc.shallow_search(lambda node: (
            "prov:used" in node and node["prov:used"] == [res.ref for res in stored_results_of_curate]
        ))[0]
        mapped_metadata = prov_doc.shallow_search(lambda node: (
            "prov:wasAttributedTo" in node and node["prov:wasAttributedTo"] == [deposit_plugin.ref]
        ))[0]
        store_mapped = prov_doc.shallow_search(lambda node: (
            "prov:used" in node and node["prov:used"] == [mapped_metadata.ref]
        ))[0]
        result_mapped = prov_doc.shallow_search(lambda node: (
            "prov:wasGeneratedBy" in node and node["prov:wasGeneratedBy"] == [store_mapped.ref]
        ))[0]
        updated_metadata = prov_doc.shallow_search(lambda node: (
            "prov:wasInfluencedBy" in node and node["prov:wasInfluencedBy"] == [deposit_plugin.ref]
        ))[0]
        result_updated = prov_doc.shallow_search(lambda node: (
            "prov:wasDerivedFrom" in node and node["prov:wasDerivedFrom"] == [updated_metadata.ref]
        ))[0]
        store_updated = prov_doc.shallow_search(lambda node: (
            "prov:used" in node and node["prov:used"] == [updated_metadata.ref]
        ))[0]
        map_action = prov_doc.shallow_search(lambda node: (
            "@id" in node and node["@id"] == mapped_metadata["prov:wasGeneratedBy"][0]["@id"]
        ))[0]
        # print general info and info on map as well as update of the metadata
        print(
            "  - Time consumed:\n"
            f"    - Preparation at ~{load_action['prov:endedAtTime'][0]} took ~"
            f"{map_action['prov:startedAtTime'][0]-load_action['prov:endedAtTime'][0]}\n"
            f"    - Mapping at ~{map_action['prov:startedAtTime'][0]} took ~"
            f"{map_action['prov:endedAtTime'][0]-map_action['prov:startedAtTime'][0]}\n"
            f"    - Creating new or initial version and updating metadata at ~{store_mapped['prov:endedAtTime'][0]}"
            f" took ~{updated_metadata['prov:generatedAtTime'][0]-store_mapped['prov:endedAtTime'][0]}\n"
            f"    - Deletion of artifacts, upload of artifacts and publication at"
            f" ~{store_updated['prov:endedAtTime'][0]} took N/A\n"
            f"  - Curated metadata loaded (at {load_action['prov:startedAtTime'][0]}"
            f", took {load_action['prov:endedAtTime'][0]-load_action['prov:startedAtTime'][0]}"
            ", may have been overwritten) from:"
        )
        for source in stored_results_of_curate:
            print(4*" " + f"- {source['schema:url'][0]} ({source['schema:description'][0].split(' ')[1]})")
        # print info on the store of the mapped as well as updated metadata
        print(
            f"  - Metadata mapped for deposit stored (at {store_mapped['prov:startedAtTime'][0]}, took "
            f"{store_mapped['prov:endedAtTime'][0]-store_mapped['prov:startedAtTime'][0]}) in:\n"
            f"    - {result_mapped['schema:url'][0]}\n"
            f"  - Metadata updated after deposit stored (at {store_updated['prov:startedAtTime'][0]}, took "
            f"{store_updated['prov:endedAtTime'][0]-store_updated['prov:startedAtTime'][0]}) in:\n"
            f"    - {result_updated['schema:url'][0]}"
        )

    def report_postprocess(self: Self) -> None:
        """
        Print the report for the harvest step.

        Returns:
            None:
        """
        print("- Postprocess:")
        # load provenance data or error out
        ctx = HermesCacheManager()
        ctx.prepare_step("postprocess")
        with ctx["provenance"] as cache:
            try:
                prov_doc = ld_prov_list.load_ld_prov_list(cache["result"])
            except KeyError:
                print("No provenance data has been recorded so far.")
                return
            finally:
                ctx.finalize_step("postprocess")
        # get basic hermes objects
        cache = prov_doc.get_hermes_cache()
        command = prov_doc.get_hermes_command("postprocess")
        base_plugin = prov_doc.get_hermes_base_plugin("postprocess")
        # print info on the plugin
        plugin = prov_doc.shallow_search(lambda node: (
            "prov:actedOnBehalfOf" in node and node["prov:actedOnBehalfOf"] == [base_plugin.ref]
        ))[0]
        print(
            f"  - Plugin used:\n    - {plugin['@id'][28]} ({plugin['schema:name'][0]}, version "
            f"{vers if (vers := plugin.get('schema:softwareVersion', False)) else 'N/A'})"
        )
        cache_loads = prov_doc.shallow_search(lambda node: (
            "prov:wasAssociatedWith" in node and
            node["prov:wasAssociatedWith"] == [plugin.ref, base_plugin.ref, command.ref, cache.ref]
        ))
        # print info on the loads from cache
        print("  - Used deposit results:")
        for index, cache_load in enumerate(cache_loads, start=1):
            source_id = cache_load["prov:used"][0]["@id"]
            source = prov_doc.shallow_search(lambda node: ("@id" in node and node["@id"] == [source_id]))[0]
            print(
                f"    - Load {index} at {cache_load['prov:startedAtTime']} took "
                f"{cache_load['prov:endedAtTime']-cache_load['prov:startedAtTime']} from:\n"
                f"      - {source['schema:url']}"
            )
        io_ops = prov_doc.shallow_search(lambda node: (
            "prov:wasAssociatedWith" in node and
            node["prov:wasAssociatedWith"] == [plugin.ref, base_plugin.ref, command.ref]
        ))
        # sort io operations into load and write operations
        loads, writes = [], []
        for io_op in io_ops:
            used = io_op["prov:used"][0]["@id"]
            if "prov:wasDerivedFrom" in prov_doc.shallow_search(lambda node: ("@id" in node and node["@id"] == used)):
                writes.append(io_op)
            else:
                loads.append(io_op)
        # print info on general loads of the plugin
        print("  - Loaded data from:")
        for index, load in enumerate(loads):
            source_id = load["prov:used"][0]["@id"]
            source = prov_doc.shallow_search(lambda node: ("@id" in node and node["@id"] == [source_id]))[0]
            print(
                f"    - Load {index} at {load['prov:startedAtTime']} took "
                f"{load['prov:endedAtTime']-load['prov:startedAtTime']} from:\n"
                f"      - {source['schema:url']}"
            )
        # print info on general writes of the plugin
        print("  - Written data to:")
        for index, write in enumerate(writes):
            target = prov_doc.shallow_search(lambda node: (
                "prov:wasGeneratedBy" in node and node["prov:wasGeneratedBy"] == [write.ref]
            ))[0]
            print(
                f"    - Load {index} at {write['prov:startedAtTime']} took "
                f"{write['prov:endedAtTime']-write['prov:startedAtTime']} from:\n"
                f"      - {target['schema:url']}"
            )
