import collections
import contextlib
import itertools

import aiopoke
import networkx
from aiopoke.utils.minimal_resources import MinimalResource


class AiopokeClient(aiopoke.AiopokeClient):
    def __init__(self, *, session=None) -> None:
        super().__init__(session=session)

        self._all_species: list[MinimalResource[aiopoke.PokemonSpecies]] = []
        self._evolution_stages: dict[int, int] = {}  # species_id -> stage

    async def all_pokemon_species(self):
        if self._all_species:
            return self._all_species

        response = await self.http.get('pokemon-species/?limit=2147483647')

        for data in response['results']:
            res = MinimalResource[aiopoke.PokemonSpecies](**data)
            res._client = self
            self._all_species.append(res)

        return self._all_species

    async def evolution_stage(self, species: aiopoke.PokemonSpecies) -> int:
        with contextlib.suppress(KeyError):
            return self._evolution_stages[species.id]

        chain = await species.evolution_chain.fetch(client=self)
        links = [chain.chain]

        for current_stage in itertools.count(1):
            if not links:
                break

            successors = []

            for source in links:
                self._evolution_stages.setdefault(
                    source.species.id,
                    current_stage,
                )
                successors.extend(source.evolves_to)

            links = successors

        return self._evolution_stages[species.id]


async def evolution_graph(
    species: aiopoke.PokemonSpecies,
    /,
) -> networkx.DiGraph:
    evolution_chain = await species.evolution_chain.fetch()

    links = collections.deque([evolution_chain.chain])
    graph = networkx.DiGraph()

    while links:
        source = links.popleft()

        for target in source.evolves_to:
            graph.add_edge(source.species, target.species)
            links.append(target)

    return graph
